import React from "react";

const LogsTable = ({ columns, sortedLogs, handleSort, sortConfig, handleCellDoubleClick, formatCell }) => (
  <div className="overflow-x-auto">
    <table className="min-w-full border-collapse border border-gray-300">
      <thead>
        <tr className="bg-gray-200">
          {columns.map((col, index) => (
            <th
              key={index}
              className="border p-2 cursor-pointer"
              onClick={() => handleSort(col)}
            >
              {col.toLowerCase().replace("_", " ").toUpperCase()}
              {sortConfig.key === col && (
                <span>{sortConfig.direction === "asc" ? " ↑" : " ↓"}</span>
              )}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sortedLogs.map((log, index) => (
          <tr key={index} className="border">
            {columns.map((col, idx) => (
              <td
                key={idx}
                className="border p-2"
                onDoubleClick={() => handleCellDoubleClick(col, log[col])}
              >
                {formatCell(log[col])}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

export default LogsTable;
