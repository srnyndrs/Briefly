export type Article = {
  id: string;
  title: string;
  sourceId?: string;
  publishedAt?: string;
  language?: string;
  categories: string[];
  imageRef?: string;
  url?: string;
  sentiment?: string;
  contentRef?: string;
  clusterId?: string;
  modelVersion?: string;
};

export type PaginatedArticles = {
  items: Article[];
  total: number;
  limit: number;
  offset: number;
};
