import { useState, useEffect } from "react";

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

  const handleChange = (e) => {
    setFilterText(e.target.value);
  };

  const handleOperatorChange = (index, newOperator) => {
    const updatedFilters = filters.map((filter, i) =>
      i === index ? { ...filter, operator: newOperator } : filter
    );
    updateFilterText(updatedFilters);
  };

  const handleComparisonChange = (index, newComparison) => {
    const updatedFilters = filters.map((filter, i) =>
      i === index ? { ...filter, comparison: newComparison } : filter
    );
    updateFilterText(updatedFilters);
  };

  const handleFieldChange = (index, newField) => {
    const updatedFilters = filters.map((filter, i) =>
      i === index ? { ...filter, field: newField, value: "" } : filter // Reset value when field changes
    );
    updateFilterText(updatedFilters);
  };

  const handleValueChange = (index, newValue) => {
    const updatedFilters = filters.map((filter, i) =>
      i === index ? { ...filter, value: newValue } : filter
    );
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

  return (
    <div className="filter-input-container">
      <input
        type="text"
        value={filterText}
        onChange={handleChange}
        placeholder="Enter filters (e.g., id == 2289 AND status == 'active')"
        className="filter-input"
      />
      <div className="mt-2 flex flex-wrap items-center gap-x-2">
        {filters.map((filter, index) => (
          <div key={index} className="filter-row">
            {index > 0 && (
              <select
                value={filter.operator || "AND"}
                onChange={(e) => handleOperatorChange(index, e.target.value)}
                className="operator-dropdown"
              >
                <option value="AND">AND</option>
                <option value="OR">OR</option>
                <option value="NAND">NAND</option>
                <option value="XOR">XOR</option>
              </select>
            )}
            <select
              value={filter.field}
              onChange={(e) => handleFieldChange(index, e.target.value)}
              className="filter-dropdown"
            >
              {fieldOptions && Object.keys(fieldOptions).map((field) => (
                <option key={field} value={field}>{field}</option>
              ))}
            </select>
            <select
              value={filter.comparison}
              onChange={(e) => handleComparisonChange(index, e.target.value)}
              className="filter-dropdown"
            >
              <option value="==">==</option>
              <option value="!=">!=</option>
              <option value=">">{">"}</option>
              <option value="<">{"<"}</option>
            </select>
            <select
              value={filter.value}
              onChange={(e) => handleValueChange(index, e.target.value)}
              disabled={!filter.field}
              className="filter-dropdown"
            >
              {filter.field && fieldOptions[filter.field]?.map((value) => (
                <option key={value} value={value}>{value}</option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </div>
  );

};

export default FilterInput;
