export type Book = {
  id: number;
  title: string;
  author?: string;
  description?: string;
  cover_image?: string;
  purchase_link?: string;
  episode: {
    id: number;
    title: string;
    url?: string;
    aired_at?: string;
    description?: string;
    brand: {
      id: number;
      name: string;
      station: {
        id: number;
        name: string;
        station_id: string;
      };
    };
  };
};

export type Show = {
  id: number;
  name: string;
  description?: string;
  url: string;
  station: {
    id: number;
    name: string;
    station_id: string;
  };
  book_count: number;
};

export type Station = {
  id: number;
  name: string;
  station_id: string;
  url: string;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

