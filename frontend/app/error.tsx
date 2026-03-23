'use client'

import { useEffect } from 'react'

export default function GlobalError({ error }: { error: Error }) {
  useEffect(() => {
    if (error?.message?.includes('ChunkLoadError')) {
      console.warn('Chunk error → reload')
      window.location.reload()
    }
  }, [error])

  return (
    <html>
      <body>
        <h2>Something went wrong</h2>
      </body>
    </html>
  )
}
