# Genos

A local-first project assistant that can attach to one software workspace at a time.

## What it does

- Understands the active project
- Reads and searches project files
- Inspects Git state and history
- Tracks project goals
- Stores project-specific memory
- Maintains project conversation history
- Plans work
- Requests permission before changes
- Modifies the project when approved
- Runs tests and verifies results
- Keeps separate context for separate projects

## Workspace model

`	ext
Genos
      |
      +-- Current Workspace
      |      |
      |      +-- Files
      |      +-- Git
      |      +-- Goals
      |      +-- Memory
      |      +-- Conversation
      |
      +-- Permissions
      +-- Tools
      +-- Verification
`

The helper is not permanently tied to one project.

## Permission model

The active workspace is the default security boundary.

`	ext
READ
SAFE_WRITE
EXECUTE
DESTRUCTIVE
`

Read operations can be automatic. Changes and potentially dangerous operations require appropriate user permission.

## Action model

`	ext
understand
   |
plan
   |
permission
   |
act
   |
test
   |
verify
   |
report
   |
remember
`

Genos must not report an action as successful without verification.

## Offline-first

Core project functionality should work without internet access:

- file inspection
- file search
- Git inspection
- project memory
- goals
- conversation history
- approved local actions
- verification

A local AI model may be added later for natural-language reasoning, but cloud AI is not required by the core architecture.

## Development

Build incrementally.

Every major feature must have tests, documentation, local verification, and a Git milestone.

## Current target

Build the workspace foundation:

`	ext
attach
  |
inspect
  |
persist
  |
switch
  |
isolate project state
`
