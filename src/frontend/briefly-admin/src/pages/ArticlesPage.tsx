import { useQuery } from '@tanstack/react-query';
import React from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { PaginationControls } from '../components/PaginationControls';
import { getArticles } from '../lib/articles';
import { Article } from '../types/articles';

const parsePositiveInt = (value: string | null, fallback: number): number => {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
};

const formatDate = (value?: string): string => {
  if (!value) {
    return 'Unknown publish date';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
};

const ArticleCard = ({ article, featured = false }: { article: Article; featured?: boolean }) => {
  return (
    <Link
      className={[
        'group block overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:shadow-md',
        featured ? 'lg:p-7' : '',
      ].join(' ')}
      to={`/articles/${article.id}`}
    >
      <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span>{article.sourceId || 'Unknown source'}</span>
        <span>•</span>
        <span>{formatDate(article.publishedAt)}</span>
      </div>
      <h2
        className={[
          'font-bold tracking-tight text-slate-900 transition group-hover:text-slate-700',
          featured ? 'text-2xl sm:text-3xl' : 'text-lg',
        ].join(' ')}
      >
        {article.title}
      </h2>
      <div className="mt-3 flex flex-wrap gap-2">
        {article.categories.slice(0, 3).map((category) => (
          <span
            className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
            key={category}
          >
            {category}
          </span>
        ))}
      </div>
      {article.imageRef ? (
        <div className="mt-4 rounded-xl bg-slate-100 p-3 text-xs text-slate-500">
          image_ref: {article.imageRef}
        </div>
      ) : null}
    </Link>
  );
};

export const ArticlesPage = (): React.JSX.Element => {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = parsePositiveInt(searchParams.get('page'), 1);
  const pageSize = parsePositiveInt(searchParams.get('pageSize'), 20);
  const query = searchParams.get('q')?.trim() || '';
  const offset = (page - 1) * pageSize;

  const [inputValue, setInputValue] = React.useState(query);

  React.useEffect(() => {
    setInputValue(query);
  }, [query]);

  const articleQuery = useQuery({
    queryKey: ['articles', { page, pageSize, query }],
    queryFn: () => getArticles({ limit: pageSize, offset, query: query || undefined }),
    placeholderData: (previousData) => previousData,
  });

  const setListParams = (next: { page?: number; pageSize?: number; q?: string }) => {
    const nextPage = next.page ?? page;
    const nextPageSize = next.pageSize ?? pageSize;
    const nextQuery = next.q ?? query;

    const updated = new URLSearchParams();
    updated.set('page', String(nextPage));
    updated.set('pageSize', String(nextPageSize));
    if (nextQuery) {
      updated.set('q', nextQuery);
    }

    setSearchParams(updated);
  };

  const items = articleQuery.data?.items ?? [];
  const featured = items[0];
  const secondary = items.slice(1, 7);
  const rail = items.slice(7);

  return (
    <section>
      <div className="mb-6 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white/90 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Latest Articles</h2>
          <p className="text-sm text-slate-600">Read-only editorial view for feed entries.</p>
        </div>
        <form
          className="flex w-full max-w-md gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            setListParams({ page: 1, q: inputValue.trim() });
          }}
        >
          <input
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            onChange={(event) => setInputValue(event.target.value)}
            placeholder="Search articles"
            value={inputValue}
          />
          <button
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white"
            type="submit"
          >
            Search
          </button>
        </form>
      </div>

      {articleQuery.isLoading ? <p className="text-slate-600">Loading articles...</p> : null}
      {articleQuery.isError ? (
        <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to load articles. Check API base URL and network access.
        </p>
      ) : null}

      {!articleQuery.isLoading && !articleQuery.isError ? (
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <div className="space-y-6">
            {featured ? <ArticleCard article={featured} featured /> : null}
            <div className="grid gap-4 sm:grid-cols-2">
              {secondary.map((article) => (
                <ArticleCard article={article} key={article.id} />
              ))}
            </div>
          </div>

          <aside className="rounded-2xl border border-slate-200 bg-white p-4">
            <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
              Headline Rail
            </h3>
            <ul className="space-y-3">
              {rail.map((article) => (
                <li className="border-b border-slate-100 pb-3 last:border-0 last:pb-0" key={article.id}>
                  <Link className="font-medium text-slate-800 hover:text-slate-600" to={`/articles/${article.id}`}>
                    {article.title}
                  </Link>
                  <p className="mt-1 text-xs text-slate-500">{formatDate(article.publishedAt)}</p>
                </li>
              ))}
            </ul>
          </aside>
        </div>
      ) : null}

      <PaginationControls
        onPageChange={(nextPage) => setListParams({ page: Math.max(1, nextPage) })}
        onPageSizeChange={(nextPageSize) => setListParams({ page: 1, pageSize: nextPageSize })}
        page={page}
        pageSize={pageSize}
        total={articleQuery.data?.total ?? 0}
      />
    </section>
  );
};
