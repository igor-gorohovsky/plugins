-- rex_wait_worker.lua: wait until one worker's turn ends. istack-worker runs it under Rex.
--
--   rex do -s <session id> -b <block id> rex_wait_worker.lua [timeout=540] [after=<updated_at>]
--
-- -s is needed when the block is in another session than the caller's: Rex looks for it only there.
--
-- Returns {"status": "done" | "blocked" | "error" | "idle" | "exited" | "working", ...}; "working" means the timeout
-- passed. "idle" is an agent that has sat at its prompt for a while: the user interrupted it, or it never started.
-- It is also an agent that ccw holds suspended with no record of its last turn, as after `ccw restore` brought it
-- back from a Rex server restart: no turn runs until a line wakes it.
-- "exited" is also a tab that fell back to a bare shell (a Rex server restart restores every tab as a shell).
-- The state is read from the terminal's current program-status record (OSC 7501) and its exit code, so a turn
-- that ended before the wait started is not missed. `after` is the updated_at of the record that was current
-- when a follow-up message was typed: that record belongs to the turn before and is ignored.
-- A call that fails ends the script with an error; it is never reported as "working".
local TERM = "com.superlogical.terminal"
-- The states that end a turn, and the rule for idle; lib/terminals.lua of the esh plugin has the same ones.
local FINAL_STATES = { done = true, blocked = true, error = true }
local IDLE_SECONDS = 20
local SHELLS = { bash = true, zsh = true, sh = true, fish = true, dash = true }
-- ccw reports an agent it suspended as a child record with this id, in state idle; it clears the record on wake.
local CCW_RECORD = "ccw"
local POLL_SECONDS = 2
local block = assert(rex.block_id, "run with -b <block id>")
local after = rex.args.after and tostring(rex.args.after) or nil
local target = { block_id = block }

local function call_block(method)
  local result, err = rex.block.call(TERM, method, target)
  if result == nil then error(method .. ": " .. tostring(err), 0) end
  return result
end

-- An agent that was just started is idle for a moment; one that stays idle is not going to work by itself.
local function check_idle_for_long(record)
  local year, month, day, hour, minute, second = tostring(record.updated_at):match("^(%d+)-(%d+)-(%d+)T(%d+):(%d+):(%d+)")
  if record.state ~= "idle" or year == nil then return false end
  local since = os.time{ year = year, month = month, day = day, hour = hour, min = minute, sec = second }
  return os.time() - since >= IDLE_SECONDS
end

local function read_state()
  local process = call_block("process")
  if process.last_exit then return { status = "exited", exit_code = process.last_exit.exit_code } end
  local child, foreground = process.child, process.foreground
  -- The login shell of an empty tab ("-bash"), running nothing: the agent that ran here is gone.
  local bare = child and foreground and child.pid == foreground.pid and SHELLS[child.name]
    and tostring(child.argv0):sub(1, 1) == "-"
  if bare then return { status = "exited" } end
  local suspended, turn_on_record = nil, false
  for _, record in ipairs(call_block("program_status").records or {}) do
    local id = record.id or ""
    if id == "" and (FINAL_STATES[record.state] or check_idle_for_long(record)) then
      if record.updated_at ~= after then
        return { status = record.state, kind = record.kind, msg = record.msg, at = record.updated_at }
      end
      turn_on_record = true
    elseif id == CCW_RECORD and record.state == "idle" and record.updated_at ~= after then
      suspended = record
    end
  end
  -- While the agent's own record holds its last turn, that record decides, so a wake still in flight is not an end.
  if suspended and not turn_on_record then
    return { status = "idle", kind = suspended.kind, msg = suspended.msg, at = suspended.updated_at }
  end
  return nil
end

local deadline = os.time() + (tonumber(rex.args.timeout) or 540)
while true do
  local state = read_state()
  if state then return state end
  if os.time() >= deadline then return { status = "working" } end
  rex.sleep(POLL_SECONDS)
end
