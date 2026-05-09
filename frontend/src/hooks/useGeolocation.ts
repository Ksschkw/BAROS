import { useState, useEffect, useCallback } from 'react'

interface GeolocationState {
  latitude: number | null
  longitude: number | null
  accuracy: number | null
  error: string | null
  loading: boolean
}

export function useGeolocation() {
  const [state, setState] = useState<GeolocationState>({
    latitude: null,
    longitude: null,
    accuracy: null,
    error: null,
    loading: true,
  })

  const getPosition = useCallback(() => {
    if (!navigator.geolocation) {
      setState({ latitude: null, longitude: null, accuracy: null,error: 'Geolocation not supported', loading: false })
      return
    }
    setState((s) => ({ ...s, loading: true }))
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setState({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
          accuracy: position.coords.accuracy,
          error: null,
          loading: false,
        })
      },
      (err) => {
        setState({
          latitude: null,
          longitude: null,
          accuracy: null,
          error: err.message,
          loading: false,
        })
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 600000 }
    )
  }, [])

  useEffect(() => {
    getPosition()
  }, [getPosition])

  return { ...state, refresh: getPosition }
}