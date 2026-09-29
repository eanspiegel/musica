export interface MetadataCandidate {
  source: string
  title: string
  artist: string
  album: string
  genre: string
  year: string
  track_number: string
  disc_number: string
  image_url?: string
  type: 'Album' | 'Single'
}
