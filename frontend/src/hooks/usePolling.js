import { useEffect, useRef, useState } from 'react'

/**
 * Poll an async function on an interval until `stopWhen` returns true.
 * Returns { data, error, loading, refresh }.
 */
export function usePolling(fetcher, { interval = 3000, stopWhen, deps = [] } = {}) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const stoppedRef = useRef(false)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    stoppedRef.current = false
    let cancelled = false
    let timer = null
    let consecutiveErrors = 0

    const tick = async () => {
      try {
        const next = await fetcher()
        if (cancelled) return
        setData(next)
        setError(null)
        setLoading(false)
        consecutiveErrors = 0
        if (stopWhen && stopWhen(next)) {
          stoppedRef.current = true
          return
        }
      } catch (err) {
        if (cancelled) return
        setError(err)
        setLoading(false)
        consecutiveErrors += 1
        // 404 = resource is gone; pointless to keep hammering it.
        // Anything else: stop after 5 consecutive failures so a flaky
        // backend or expired session doesn't spam the server forever.
        const httpStatus = err?.response?.status
        if (httpStatus === 404 || consecutiveErrors >= 5) {
          stoppedRef.current = true
          return
        }
      }
      if (!cancelled && !stoppedRef.current) {
        timer = setTimeout(tick, interval)
      }
    }

    tick()
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, deps)

  const refresh = async () => {
    setLoading(true)
    try {
      const next = await fetcher()
      setData(next)
      setError(null)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  return { data, error, loading, refresh }
}
