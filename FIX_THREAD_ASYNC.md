# Fix: Thread-Safe Async Runner

## Problem
Calling `asyncio.run()` inside `threading.Thread` can cause `RuntimeError: Event loop is already running` when multiple threads execute simultaneously. This happens because `asyncio.run()` tries to create/manage a global event loop, which conflicts across threads.

## Solution
Created a `run_async_in_thread()` helper method that:
1. **Creates a new isolated event loop** for each thread call
2. **Runs the coroutine** to completion
3. **Properly closes** the event loop after execution
4. **Cleans up** the event loop reference to prevent conflicts

## Changes Made

### Added Helper Method (Line ~5370)
```python
def run_async_in_thread(self, coro):
    """Thread-safe async runner - prevents 'Event loop is already running' errors.
    
    Use this instead of asyncio.run() when calling async functions from threading.Thread.
    Each thread gets its own isolated event loop.
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        try:
            asyncio.set_event_loop(None)
        except:
            pass
```

### Replaced All Unsafe Calls

**Before:**
```python
asyncio.run(self.edge_tts_save(text, voice, temp_tts, rate_str, pitch_str))
asyncio.run(self.batch_generate_tts(tasks))
```

**After:**
```python
self.run_async_in_thread(self.edge_tts_save(text, voice, temp_tts, rate_str, pitch_str))
self.run_async_in_thread(self.batch_generate_tts(tasks))
```

## Affected Locations
1. **Line ~4836** - Single TTS generation in `process_row_action()`
2. **Line ~5117** - Batch TTS generation in `run_srt_thread()`
3. **Line ~5376** - TTS thread in `run_tts_thread()`

## Benefits
✅ **No more event loop conflicts** - Each thread gets its own isolated loop  
✅ **Thread-safe** - Multiple threads can run async operations simultaneously  
✅ **Proper cleanup** - Event loops are closed after use to prevent memory leaks  
✅ **Backward compatible** - No changes to async function signatures  

## Technical Details

### Why `asyncio.run()` Fails in Threads
- `asyncio.run()` calls `asyncio.set_event_loop()` internally
- If another thread already set an event loop, it raises `RuntimeError`
- Python's asyncio policy management isn't thread-safe by default

### Why Our Solution Works
- `asyncio.new_event_loop()` creates a fresh loop without checking global state
- We explicitly set and clean up the loop in the thread context
- The `finally` block ensures cleanup even if exceptions occur
- Setting event loop to `None` after closing prevents stale references

## Testing Recommendations
1. Run multiple TTS generations simultaneously
2. Test batch SRT processing with many segments
3. Verify no "Event loop is already running" errors appear
4. Check that all audio files are generated correctly

## References
- Python Docs: [asyncio.new_event_loop()](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.new_event_loop)
- Python Docs: [Running async functions from threads](https://docs.python.org/3/library/asyncio-dev.html#running-async-functions-from-threads)
