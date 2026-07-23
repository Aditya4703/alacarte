import { EventEmitter } from 'node:events'

const bus = new EventEmitter()
bus.setMaxListeners(100)

export function emitEvent(type, data) {
  bus.emit('event', { type, data, ts: Date.now() })
}

export function onEvent(listener) {
  bus.on('event', listener)
  return () => bus.off('event', listener)
}

/**
 * Creates a throttled emitter that batches calls by a string key.
 * Only the *latest* data for each key is emitted, at most once per `intervalMs`.
 * Perfect for high-frequency events like job.update where only the latest state matters.
 */
export function createThrottledEmitter(type, intervalMs = 300) {
  const pending = new Map() // key -> data
  let timer = null

  function flush() {
    timer = null
    if (pending.size === 0) return
    for (const [, data] of pending) {
      bus.emit('event', { type, data, ts: Date.now() })
    }
    pending.clear()
  }

  return {
    emit(key, data) {
      pending.set(key, data)
      if (!timer) {
        timer = setTimeout(flush, intervalMs)
      }
    },
    /** Force-flush any pending data immediately (e.g. on job completion). */
    flush(key) {
      if (key != null && pending.has(key)) {
        const data = pending.get(key)
        pending.delete(key)
        bus.emit('event', { type, data, ts: Date.now() })
      } else if (key == null) {
        flush()
      }
      if (pending.size === 0 && timer) {
        clearTimeout(timer)
        timer = null
      }
    },
  }
}

/**
 * Creates a batching emitter that collects items and flushes them as an array.
 * Ideal for job.log where we want to deliver lines in batches, not one by one.
 */
export function createBatchEmitter(type, intervalMs = 250) {
  const buckets = new Map() // key -> data[]
  let timer = null

  function flush() {
    timer = null
    if (buckets.size === 0) return
    for (const [, items] of buckets) {
      for (const data of items) {
        bus.emit('event', { type, data, ts: Date.now() })
      }
    }
    buckets.clear()
  }

  return {
    push(key, data) {
      let arr = buckets.get(key)
      if (!arr) {
        arr = []
        buckets.set(key, arr)
      }
      arr.push(data)
      if (!timer) {
        timer = setTimeout(flush, intervalMs)
      }
    },
    flush(key) {
      if (key != null && buckets.has(key)) {
        const items = buckets.get(key)
        buckets.delete(key)
        if (items) {
          for (const data of items) {
            bus.emit('event', { type, data, ts: Date.now() })
          }
        }
      } else if (key == null) {
        flush()
      }
      if (buckets.size === 0 && timer) {
        clearTimeout(timer)
        timer = null
      }
    },
  }
}
