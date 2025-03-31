import { useState, useEffect } from "react";

const FilterInput = ({ filterText, setFilterText }) => {
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
    <div className="p-4 border rounded w-full">
      <input
        type="text"
        value={filterText}
        onChange={handleChange}
        placeholder="Enter filters (e.g., id == 2289 AND status == 'active')"
        className="border p-2 w-full min-w-[800px] max-w-[1000px]"
        style={{ width: "100%" }}
      />
      <div className="mt-2 flex flex-wrap items-center gap-x-2">
        {filters.map((filter, index) => (
          <div key={index} className="flex items-center space-x-2">
            {index > 0 && (
              <select
                value={filter.operator || "AND"}
                onChange={(e) => handleOperatorChange(index, e.target.value)}
                className="bg-white text-gray-700"
                style={{
                  appearance: "none",
                  backgroundColor: "transparent",
                  padding: "0 8px", // Add space on left and right
                  width: "auto",
                  minWidth: "fit-content",
                  border: "none",
                  fontSize: "inherit",
                  fontFamily: "inherit",
                  fontWeight: "inherit",
                  color: "inherit",
                  textAlign: "center",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <option value="AND">AND</option>
                <option value="OR">OR</option>
                <option value="NAND">NAND</option>
                <option value="XOR">XOR</option>
              </select>
            )}
            <span className="border p-2 min-w-[150px] w-auto">{filter.field}</span>
            <select
              value={filter.comparison}
              onChange={(e) => handleComparisonChange(index, e.target.value)}
              className="bg-white text-gray-700"
              style={{
                appearance: "none",
                backgroundColor: "transparent",
                padding: "0 8px", // Add space on left and right
                width: "auto",
                minWidth: "fit-content",
                border: "none",
                fontSize: "inherit",
                fontFamily: "inherit",
                fontWeight: "inherit",
                color: "inherit",
                textAlign: "center",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <option value="==">==</option>
              <option value="!=">!=</option>
              <option value=">">{">"}</option>
              <option value="<">{"<"}</option>
            </select>
            <span className="border p-2 min-w-[150px] w-auto">{filter.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default FilterInput;
