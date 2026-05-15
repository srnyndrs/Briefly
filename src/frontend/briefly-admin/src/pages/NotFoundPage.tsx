import React from 'react';
import { Link } from 'react-router-dom';

export const NotFoundPage = (): React.JSX.Element => {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6">
      <h2 className="text-xl font-semibold text-slate-900">Page not found</h2>
      <p className="mt-2 text-sm text-slate-600">The requested route does not exist.</p>
      <Link className="mt-4 inline-block text-sm font-semibold text-slate-800" to="/articles">
        Go to articles
      </Link>
    </section>
  );
};
