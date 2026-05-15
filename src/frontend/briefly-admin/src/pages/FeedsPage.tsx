import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import React from 'react';
import { createSource, deleteSource, exploreSources, listSources } from '../lib/feeds';

const formatDateTime = (value?: string): string => {
  if (!value) {
    return 'N/A';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
};

export const FeedsPage = (): React.JSX.Element => {
  const queryClient = useQueryClient();
  const [exploreUrl, setExploreUrl] = React.useState('');
  const [createUrl, setCreateUrl] = React.useState('');
  const [createTitle, setCreateTitle] = React.useState('');
  const [exploreResults, setExploreResults] = React.useState<
    Array<{
      url: string;
      title?: string;
      description?: string;
      contentType?: string;
    }>
  >([]);

  const feedsQuery = useQuery({
    queryKey: ['sources'],
    queryFn: listSources,
  });

  const exploreMutation = useMutation({
    mutationFn: exploreSources,
    onSuccess: (results) => {
      setExploreResults(results);
    },
  });

  const createMutation = useMutation({
    mutationFn: createSource,
    onSuccess: () => {
      setCreateUrl('');
      setCreateTitle('');
      void queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSource,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['sources'] });
    },
  });

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Feeds</h2>
          <p className="text-sm text-slate-600">Manage crawl sources and discover new feed URLs.</p>
        </div>
        <div className="grid w-full gap-2 rounded-2xl border border-slate-200 bg-white p-3 sm:w-auto sm:min-w-[380px]">
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (!exploreUrl.trim()) {
                return;
              }
              exploreMutation.mutate(exploreUrl.trim());
            }}
          >
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              onChange={(event) => setExploreUrl(event.target.value)}
              placeholder="Explore URL (https://example.com)"
              value={exploreUrl}
            />
            <button
              className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-semibold text-white"
              disabled={exploreMutation.isPending}
              type="submit"
            >
              Explore
            </button>
          </form>

          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (!createUrl.trim()) {
                return;
              }
              createMutation.mutate({
                url: createUrl.trim(),
                title: createTitle.trim() || undefined,
              });
            }}
          >
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              onChange={(event) => setCreateUrl(event.target.value)}
              placeholder="Create feed URL"
              value={createUrl}
            />
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              onChange={(event) => setCreateTitle(event.target.value)}
              placeholder="Optional title"
              value={createTitle}
            />
            <button
              className="rounded-lg bg-blue-700 px-3 py-2 text-sm font-semibold text-white"
              disabled={createMutation.isPending}
              type="submit"
            >
              Create
            </button>
          </form>
        </div>
      </div>

      {exploreResults.length > 0 ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-4">
          <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Explore Results
          </h3>
          <ul className="space-y-2">
            {exploreResults.map((result) => (
              <li className="rounded-lg border border-slate-100 p-3" key={result.url}>
                <p className="font-semibold text-slate-900">{result.title || result.url}</p>
                <p className="text-xs text-slate-600">{result.url}</p>
                {result.description ? (
                  <p className="mt-1 text-sm text-slate-700">{result.description}</p>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {feedsQuery.isError ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          Failed to load feeds.
        </div>
      ) : null}

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Feed ID</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Name</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">URL</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Status</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Updated</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {(feedsQuery.data || []).map((feed) => (
              <tr key={feed.feedId}>
                <td className="px-4 py-3 text-slate-700">{feed.feedId}</td>
                <td className="px-4 py-3 text-slate-700">{feed.title || 'Untitled feed'}</td>
                <td className="max-w-[320px] truncate px-4 py-3 text-slate-700">{feed.url}</td>
                <td className="px-4 py-3 text-slate-700">
                  {feed.lastCrawlSucceeded ? 'Healthy' : 'Degraded'}
                </td>
                <td className="px-4 py-3 text-slate-700">{formatDateTime(feed.updatedAt)}</td>
                <td className="px-4 py-3 text-slate-700">
                  <button
                    className="rounded-lg border border-red-300 px-2 py-1 text-xs font-semibold text-red-700"
                    disabled={deleteMutation.isPending}
                    onClick={() => deleteMutation.mutate(feed.feedId)}
                    type="button"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
            {!feedsQuery.isLoading && (feedsQuery.data || []).length === 0 ? (
              <tr>
                <td className="px-4 py-3 text-slate-500" colSpan={6}>
                  No feeds found.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
};
