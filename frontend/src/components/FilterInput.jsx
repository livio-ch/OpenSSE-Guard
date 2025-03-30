import { useState, useEffect } from "react";

const FilterInput = ({ filterText, setFilterText }) => {
  const [filters, setFilters] = useState([]);

  // Function to parse the filter text and split by AND/OR
  const parseFilterText = (text) => {
    const parts = text.split(/\s+(AND|OR)\s+/i);
    let newFilters = [];
    let lastOperator = null;

    parts.forEach((part) => {
      if (part.toUpperCase() === "AND" || part.toUpperCase() === "OR") {
        lastOperator = part.toUpperCase();
      } else {
        newFilters.push({ condition: part, operator: lastOperator });
      }
    });

    setFilters(newFilters);
  };

  // Automatically parse filters whenever filterText changes
  useEffect(() => {
    parseFilterText(filterText);
  }, [filterText]);

  // Handle text input change
  const handleChange = (e) => {
    setFilterText(e.target.value);
  };

  // Handle dropdown selection
  const handleOperatorChange = (index, newOperator) => {
    let updatedFilters = [...filters];
    updatedFilters[index].operator = newOperator;
    setFilters(updatedFilters);

    // Reconstruct the filter text
    const newText = updatedFilters
      .map((filter, i) => (i === 0 ? filter.condition : `${filter.operator} ${filter.condition}`))
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
        className="border p-2 min-w-[800px] w-full max-w-[1000px]"
        style={{ width: "100%" }}
      />
      <div className="mt-2 flex flex-wrap items-center gap-x-2">
        {filters.map((filter, index) => (
          <div key={index} className="flex items-center space-x-2">
            {index > 0 && (
              <select
                value={filter.operator || "AND"}
                onChange={(e) => handleOperatorChange(index, e.target.value)}
                className="border border-gray-300 bg-white text-gray-700 rounded-md shadow-sm text-center"
                style={{
                  appearance: 'none', // Ensure no dropdown arrow
                  backgroundColor: 'transparent', // Remove background image
                  padding: '0', // Remove padding
                  width: 'auto', // Auto width to fit text
                }}
              >
                <option value="AND">AND</option>
                <option value="OR">OR</option>
              </select>





            )}
            <span className="border p-2 min-w-[300px] w-auto">{filter.condition}</span>
          </div>
        ))}
      </div>


    </div>
  );
};

export default FilterInput;
