import React from 'react';

export const Pagination = ({ page, pages, onPageChange }) => (
  <div className="pagination">
    <button disabled={page <= 1} onClick={() => onPageChange(page - 1)}>Previous</button>
    <span>Page {page} of {pages}</span>
    <button disabled={page >= pages} onClick={() => onPageChange(page + 1)}>Next</button>
  </div>
);