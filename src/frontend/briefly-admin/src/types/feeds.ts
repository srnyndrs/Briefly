export type Source = {
  feedId: string;
  userId: string;
  url: string;
  title?: string;
  description?: string;
  favicon?: string;
  lastCrawledAt?: string;
  nextCrawlScheduledAt: string;
  lastCrawlSucceeded: boolean;
  consecutiveFailures: number;
  healthScore: number;
  createdAt: string;
  updatedAt: string;
};

export type SourceExploreResult = {
  url: string;
  title?: string;
  contentType?: string;
  favicon?: string;
  description?: string;
};
