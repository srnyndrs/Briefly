import { apiClient } from './apiClient';
import { Source, SourceExploreResult } from '../types/feeds';

type RawRecord = Record<string, unknown>;

const asString = (value: unknown): string | undefined => {
  if (typeof value === 'string' && value.trim().length > 0) {
    return value;
  }
  return undefined;
};

const asBoolean = (value: unknown, fallback = false): boolean => {
  if (typeof value === 'boolean') {
    return value;
  }
  return fallback;
};

const asNumber = (value: unknown, fallback = 0): number => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  return fallback;
};

const asArray = (value: unknown): RawRecord[] => {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is RawRecord => !!item && typeof item === 'object');
};

const normalizeSource = (raw: RawRecord): Source => ({
  feedId: asString(raw.feed_id) || 'unknown-feed',
  userId: asString(raw.user_id) || 'unknown-user',
  url: asString(raw.url) || '',
  title: asString(raw.title),
  description: asString(raw.description),
  favicon: asString(raw.favicon),
  lastCrawledAt: asString(raw.last_crawled_at),
  nextCrawlScheduledAt: asString(raw.next_crawl_scheduled_at) || '',
  lastCrawlSucceeded: asBoolean(raw.last_crawl_succeeded),
  consecutiveFailures: asNumber(raw.consecutive_failures),
  healthScore: asNumber(raw.health_score),
  createdAt: asString(raw.created_at) || '',
  updatedAt: asString(raw.updated_at) || '',
});

const normalizeExploreResult = (raw: RawRecord): SourceExploreResult => ({
  url: asString(raw.url) || '',
  title: asString(raw.title),
  contentType: asString(raw.content_type),
  favicon: asString(raw.favicon),
  description: asString(raw.description),
});

export const listSources = async (): Promise<Source[]> => {
  const response = await apiClient.get('/sources');
  return asArray(response.data).map(normalizeSource);
};

export const createSource = async (input: {
  url: string;
  title?: string;
  description?: string;
  favicon?: string;
}): Promise<Source> => {
  const response = await apiClient.post('/sources', input);
  return normalizeSource(response.data as RawRecord);
};

export const exploreSources = async (url: string): Promise<SourceExploreResult[]> => {
  const response = await apiClient.post('/sources/explore', { url });
  return asArray(response.data).map(normalizeExploreResult);
};

export const deleteSource = async (sourceId: string): Promise<void> => {
  await apiClient.delete(`/sources/${sourceId}`);
};
