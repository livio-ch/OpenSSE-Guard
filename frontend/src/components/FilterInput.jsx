import { useState, useEffect } from "react";

// Utility function to update filters based on a specific change
const updateFilter = (filters, index, field, value) => {
  const updatedFilters = [...filters];
  updatedFilters[index] = { ...updatedFilters[index], [field]: value };
  return updatedFilters;
};

const FilterInput = ({ filterText, setFilterText, fieldOptions }) => {
  const [filters, setFilters] = useState([]);

  const parseFilterText = (text) => {
    if (!text.trim()) {
      setFilters([]);
      return;
    }

    const parts = text.split(/\s+(AND|OR|NAND|XOR)\s+/i);
    let newFilters = [];
    let lastOperator = null;

    parts.forEach((part) => {
      if (["AND", "OR", "NAND", "XOR"].includes(part.toUpperCase())) {
        lastOperator = part.toUpperCase();
      } else {
        const match = part.match(/(.+?)\s*(==|!=|>|<)\s*(.+)/);
        if (match) {
          newFilters.push({
            field: match[1].trim(),
            comparison: match[2].trim(),
            value: match[3].trim(),
            operator: lastOperator,
          });
        }
      }
    });

    setFilters(newFilters);
  };

  useEffect(() => {
    parseFilterText(filterText);
  }, [filterText]);

  // Generic function to handle filter updates
  const handleFilterChange = (index, field, value) => {
    const updatedFilters = updateFilter(filters, index, field, value);
    updateFilterText(updatedFilters);
  };

  const updateFilterText = (updatedFilters) => {
    setFilters(updatedFilters);
    const newText = updatedFilters
      .map((filter, i) =>
        i === 0
          ? `${filter.field} ${filter.comparison} ${filter.value}`
          : `${filter.operator} ${filter.field} ${filter.comparison} ${filter.value}`
      )
      .join(" ");
    setFilterText(newText);
  };

  const clearFilters = () => {
    setFilters([]);
    setFilterText("");
  };

  return (
    <div className="filter-input-container">
      <input
        type="text"
        value={filterText}
        onChange={(e) => setFilterText(e.target.value)}
        placeholder="Enter filters (e.g., id == 2289 AND status == 'active')"
        className="filter-input"
        aria-label="Filter input"
      />
      <div className="mt-2 flex flex-wrap items-center gap-x-2">
        {filters.map((filter, index) => (
          <div key={index} className="filter-row">
            {index > 0 && (
              <select
                value={filter.operator || "AND"}
                onChange={(e) => handleFilterChange(index, "operator", e.target.value)}
                className="operator-dropdown"
                aria-label={`Operator for filter ${index}`}
              >
                <option value="AND">AND</option>
                <option value="OR">OR</option>
                <option value="NAND">NAND</option>
                <option value="XOR">XOR</option>
              </select>
            )}
            <select
              value={filter.field}
              onChange={(e) => handleFilterChange(index, "field", e.target.value)}
              className="filter-dropdown"
              aria-label={`Field for filter ${index}`}
            >
              {fieldOptions && Object.keys(fieldOptions).map((field) => (
                <option key={field} value={field}>{field}</option>
              ))}
            </select>
            <select
              value={filter.comparison}
              onChange={(e) => handleFilterChange(index, "comparison", e.target.value)}
              className="filter-dropdown"
              aria-label={`Comparison for filter ${index}`}
            >
              <option value="==">==</option>
              <option value="!=">!=</option>
              <option value=">">{">"}</option>
              <option value="<">{"<"}</option>
            </select>
            <select
              value={filter.value}
              onChange={(e) => handleFilterChange(index, "value", e.target.value)}
              disabled={!filter.field}
              className="filter-dropdown"
              aria-label={`Value for filter ${index}`}
            >
              {filter.field && fieldOptions[filter.field]?.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
            <button
              className="clear-filter-btn2"
              onClick={() => {
                const updatedFilters = filters.filter((_, i) => i !== index);
                updateFilterText(updatedFilters);
              }}
              aria-label={`Clear filter ${index}`}
            >
              X
            </button>
          </div>
        ))}
      </div>
      <button onClick={clearFilters} className="clear-filters-btn">
        Clear All Filters
      </button>
    </div>
  );
};

export default FilterInput;
