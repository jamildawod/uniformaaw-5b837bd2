export function debug(value: any, name: string) {
  if (value === null || value === undefined) {
    console.error("NULL DETECTED:", name)
  }
  return value
}
