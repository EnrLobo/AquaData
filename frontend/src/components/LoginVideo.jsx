import { useEffect, useRef, useState } from 'react'
import { LOGIN_VIDEO } from '../content/loginHighlights'
import { prefersReducedMotion } from '../utils/motion'

const YT_ORIGIN = 'https://www.youtube-nocookie.com'

function youtubeSrc(id, autoplay) {
  const params = new URLSearchParams({
    autoplay: autoplay ? '1' : '0',
    mute: '1',
    loop: '1',
    playlist: id,
    controls: '0',
    modestbranding: '1',
    playsinline: '1',
    rel: '0',
    disablekb: '1',
    iv_load_policy: '3',
    enablejsapi: '1',
  })
  return `${YT_ORIGIN}/embed/${id}?${params}`
}

export default function LoginVideo({ paused }) {
  const iframeRef = useRef(null)
  const videoRef = useRef(null)
  const [iframeSrc] = useState(() =>
    LOGIN_VIDEO.youtubeId ? youtubeSrc(LOGIN_VIDEO.youtubeId, !prefersReducedMotion()) : '',
  )

  useEffect(() => {
    iframeRef.current?.contentWindow?.postMessage(
      JSON.stringify({ event: 'command', func: paused ? 'pauseVideo' : 'playVideo', args: '' }),
      YT_ORIGIN,
    )
    const video = videoRef.current
    if (video) {
      if (paused) video.pause()
      else video.play().catch(() => {})
    }
  }, [paused])

  if (iframeSrc) {
    return (
      <iframe
        ref={iframeRef}
        src={iframeSrc}
        title="Vídeo decorativo de fundo"
        aria-hidden="true"
        tabIndex={-1}
        allow="autoplay; encrypted-media"
        referrerPolicy="strict-origin-when-cross-origin"
        className="pointer-events-none absolute left-1/2 top-1/2 aspect-video h-full min-w-full -translate-x-1/2 -translate-y-1/2 border-0"
      />
    )
  }

  if (LOGIN_VIDEO.src) {
    return (
      <video
        ref={videoRef}
        src={LOGIN_VIDEO.src}
        poster={LOGIN_VIDEO.poster || undefined}
        muted
        loop
        playsInline
        autoPlay={!prefersReducedMotion()}
        aria-hidden="true"
        className="absolute inset-0 size-full object-cover"
      />
    )
  }

  return (
    <div
      aria-hidden="true"
      className="absolute inset-0 bg-gradient-to-br from-[#0b3a57] via-[#0a2c45] to-[#071a29]"
    />
  )
}