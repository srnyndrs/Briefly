import { apiClient } from './apiClient';
import { Article, PaginatedArticles } from '../types/articles';

type RawRecord = Record<string, unknown>;

const asString = (value: unknown): string | undefined => {
  if (typeof value === 'string' && value.trim().length > 0) {
    return value;
  }
  return undefined;
};

const asStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => asString(item))
    .filter((item): item is string => Boolean(item));
};

const asNumber = (value: unknown, fallback: number): number => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === 'string') {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return fallback;
};

const normalizeArticle = (raw: RawRecord): Article => {
  const id =
    asString(raw.article_id) ||
    asString(raw.id) ||
    asString(raw.uuid) ||
    'unknown-article';

  const title = asString(raw.title) || 'Untitled article';

  return {
    id,
    title,
    sourceId: asString(raw.source_id),
    publishedAt: asString(raw.published_at),
    language: asString(raw.language),
    categories: asStringArray(raw.categories),
    imageRef: asString(raw.image_ref),
    url: asString(raw.url) || asString(raw.canonical_url),
    sentiment: asString(raw.sentiment),
    contentRef: asString(raw.content_ref),
    clusterId: asString(raw.cluster_id),
    modelVersion: asString(raw.model_version),
  };
};

const parseItems = (data: unknown): RawRecord[] => {
  if (Array.isArray(data)) {
    return data.filter((item): item is RawRecord => !!item && typeof item === 'object');
  }

  if (!data || typeof data !== 'object') {
    return [];
  }

  const record = data as RawRecord;
  const candidates = [record.items, record.articles, record.results, record.data];

  for (const candidate of candidates) {
    if (Array.isArray(candidate)) {
      return candidate.filter(
        (item): item is RawRecord => !!item && typeof item === 'object'
      );
    }
  }

  return [];
};

const parsePaginatedArticles = (
  data: unknown,
  defaultLimit: number,
  defaultOffset: number
): PaginatedArticles => {
  const items = parseItems(data).map(normalizeArticle);
  const record = (data && typeof data === 'object' ? data : {}) as RawRecord;

  const limit = asNumber(record.limit, defaultLimit);
  const offset = asNumber(record.offset, defaultOffset);
  const total = asNumber(record.total, items.length + offset);

  return {
    items,
    total,
    limit,
    offset,
  };
};

export const getArticles = async ({
  limit,
  offset,
  query,
}: {
  limit: number;
  offset: number;
  query?: string;
}): Promise<PaginatedArticles> => {
  if (query && query.trim().length > 0) {
    const response = await apiClient.get('/feed/search', {
      params: { q: query, limit, offset },
    });
    return parsePaginatedArticles(response.data, limit, offset);
  }

  const [listResponse, countResponse] = await Promise.all([
    apiClient.get('/admin/articles', {
      params: { limit, skip: offset },
    }),
    apiClient.get('/admin/articles/count'),
  ]);

  const items = parseItems(listResponse.data).map(normalizeArticle);
  const countData =
    countResponse.data && typeof countResponse.data === 'object'
      ? (countResponse.data as RawRecord)
      : {};
  const total = asNumber(countData.count, items.length + offset);

  return {
    items,
    total,
    limit,
    offset,
  };
};

export const getArticleById = async (articleId: string): Promise<Article> => {
  const response = await apiClient.get(`/admin/articles/${articleId}`);
  const payload = response.data;

  if (!payload || typeof payload !== 'object') {
    return {
      id: articleId,
      title: 'Article not found',
      categories: [],
    };
  }

  const record = payload as RawRecord;
  const base =
    (record.item && typeof record.item === 'object' ? (record.item as RawRecord) : null) ||
    (record.data && typeof record.data === 'object' ? (record.data as RawRecord) : null) ||
    record;

  return normalizeArticle({ ...base, article_id: articleId });
};
