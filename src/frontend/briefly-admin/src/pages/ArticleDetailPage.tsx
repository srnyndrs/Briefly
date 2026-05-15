import { useQuery } from '@tanstack/react-query';
import React from 'react';
import { Link, useParams } from 'react-router-dom';
import { getArticleById } from '../lib/articles';

const LabelValue = ({ label, value }: { label: string; value?: string }): React.JSX.Element => (
  <div className="rounded-xl border border-slate-200 bg-white p-3">
    <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
    <p className="mt-1 text-sm text-slate-800">{value || 'N/A'}</p>
  </div>
);

export const ArticleDetailPage = (): React.JSX.Element => {
  const { id = '' } = useParams();
  const detailQuery = useQuery({
    queryKey: ['article-detail', id],
    queryFn: () => getArticleById(id),
    enabled: id.length > 0,
  });

  if (!id) {
    return <p className="text-sm text-red-700">Invalid article id.</p>;
  }

  if (detailQuery.isLoading) {
    return <p className="text-slate-600">Loading article details...</p>;
  }

  if (detailQuery.isError || !detailQuery.data) {
    return (
      <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Failed to load article detail.
      </p>
    );
  }

  const article = detailQuery.data;

  return (
    <section className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">Article Details</h2>
        <Link className="text-sm font-semibold text-slate-700 hover:text-slate-900" to="/articles">
          Back to Articles
        </Link>
      </div>

      <article className="rounded-2xl border border-slate-200 bg-white p-6">
        <h3 className="text-xl font-bold text-slate-900">{article.title}</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          {article.categories.map((category) => (
            <span
              className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600"
              key={category}
            >
              {category}
            </span>
          ))}
        </div>
        {article.url ? (
          <a
            className="mt-4 inline-block text-sm font-semibold text-blue-700 hover:text-blue-900"
            href={article.url}
            rel="noreferrer"
            target="_blank"
          >
            Open canonical URL
          </a>
        ) : null}
      </article>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <LabelValue label="Source ID" value={article.sourceId} />
        <LabelValue label="Published At" value={article.publishedAt} />
        <LabelValue label="Language" value={article.language} />
        <LabelValue label="Sentiment" value={article.sentiment} />
        <LabelValue label="Content Ref" value={article.contentRef} />
        <LabelValue label="Image Ref" value={article.imageRef} />
        <LabelValue label="Cluster ID" value={article.clusterId} />
        <LabelValue label="Model Version" value={article.modelVersion} />
      </div>
    </section>
  );
};
