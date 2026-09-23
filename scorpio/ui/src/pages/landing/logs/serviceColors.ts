const serviceColors = [
  "#ec9f24",
  "#4f7ee8",
  "#a45ee5",
  "#18a47b",
  "#df5c78",
  "#3a9db8",
  "#bf6b32",
  "#6c70d9",
];

export function getServiceColor(service: string): string {
  let hash = 0;
  for (const character of service) {
    hash = ((hash << 5) - hash + character.charCodeAt(0)) | 0;
  }
  return serviceColors[(hash >>> 0) % serviceColors.length];
}
