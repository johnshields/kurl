export interface Platform {
  id: string;
  name: string;
  colour: string;
}

export const platforms: Platform[] = [
  { id: "spotify", name: "Spotify", colour: "var(--color-spotify)" },
  { id: "appleMusic", name: "Apple Music", colour: "var(--color-apple-music)" },
  { id: "youtubeMusic", name: "YouTube Music", colour: "var(--color-youtube-music)" },
  { id: "deezer", name: "Deezer", colour: "var(--color-deezer)" },
  { id: "tidal", name: "Tidal", colour: "var(--color-tidal)" },
  { id: "amazonMusic", name: "Amazon Music", colour: "var(--color-amazon-music)" },
  { id: "pandora", name: "Pandora", colour: "var(--color-pandora)" },
];
