import React from 'react';

export const PaginationControls = ({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (pageSize: number) => void;
}): React.JSX.Element => {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const currentPage = Math.min(page, totalPages);

  return (
    <div className="mt-8 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white/90 p-4 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-sm text-slate-600">
        Showing page <span className="font-semibold text-slate-900">{currentPage}</span> of{' '}
        <span className="font-semibold text-slate-900">{totalPages}</span> ({total} items)
      </p>
      <div className="flex flex-wrap items-center gap-3">
        <label className="text-sm text-slate-600" htmlFor="page-size-select">
          Page size
        </label>
        <select
          id="page-size-select"
          className="rounded-lg border border-slate-300 px-2 py-1 text-sm"
          value={pageSize}
          onChange={(event) => onPageSizeChange(Number(event.target.value))}
        >
          {[10, 20, 30, 50].map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>

        <button
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage <= 1}
          type="button"
        >
          Previous
        </button>
        <button
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage >= totalPages}
          type="button"
        >
          Next
        </button>
      </div>
    </div>
  );
};
