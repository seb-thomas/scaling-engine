export type Book = {
  id: number;
  title: string;
  slug: string;
  author?: string;
  categories?: { slug: string; name: string }[];
  description?: string;
  cover_image?: string;
  purchase_link?: string;
  episode: {
    id: number;
    title: string;
    slug: string;
    url?: string;
    aired_at?: string;
    description?: string;
    brand: {
      id: number;
      name: string;
      slug: string;
      brand_color?: string;
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
  slug: string;
  description?: string;
  url: string;
  station: {
    id: number;
    name: string;
    station_id: string;
  };
  book_count: number;
  brand_color?: string;
};

export type Station = {
  id: number;
  name: string;
  station_id: string;
  url: string;
};

export type Topic = {
  slug: string;
  name: string;
  description?: string;
  book_count: number;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

