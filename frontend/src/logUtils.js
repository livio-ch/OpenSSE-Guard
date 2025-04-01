// logUtils.js

export const getValueFromObject = (obj, path) =>
  path.split(".").reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : undefined), obj);

export const applyFilters = (logs, filterText, getValueFromObject) => {
  if (!filterText.trim()) return logs;
  const filterArray = filterText.split(/\s+(AND|OR|XOR|NAND)\s+/i);
  const parsedFilterArray = [];
  let currentOperator = "AND";

  filterArray.forEach((term) => {
    const upperTerm = term.toUpperCase();
    if (["AND", "OR", "XOR", "NAND"].includes(upperTerm)) {
      currentOperator = upperTerm;
    } else {
      const match = term.match(/([a-zA-Z0-9_\.]+)\s*(==|!=|>|<)\s*(.*)/);
      if (match) {
        const [, column, operator, value] = match;
        parsedFilterArray.push({ column: column.toLowerCase(), operator, value, currentOperator });
      }
    }
  });

  return logs.filter((log) => {
    let result = parsedFilterArray[0]?.currentOperator === "AND" ? true : false;
    parsedFilterArray.forEach(({ column, operator, value, currentOperator }) => {
      const logValue = getValueFromObject(log, column);
      if (logValue === undefined || logValue === null) {
        result = currentOperator === "AND" ? false : result;
        return;
      }
      const parsedLogValue = isNaN(logValue) ? logValue : Number(logValue);
      const parsedFilterValue = isNaN(value) ? value : Number(value);
      let conditionMet = false;
      if (operator === "==") conditionMet = parsedLogValue == parsedFilterValue;
      else if (operator === "!=") conditionMet = parsedLogValue != parsedFilterValue;
      else if (operator === ">") conditionMet = parsedLogValue > parsedFilterValue;
      else if (operator === "<") conditionMet = parsedLogValue < parsedFilterValue;

      if (currentOperator === "AND") result = result && conditionMet;
      else if (currentOperator === "OR") result = result || conditionMet;
      else if (currentOperator === "XOR") result = (result ? 1 : 0) ^ (conditionMet ? 1 : 0) ? true : false;
      else if (currentOperator === "NAND") result = !(result && conditionMet);
    });
    return result;
  });
};

export const sortLogs = (logs, sortConfig, getValueFromObject) => {
  if (!sortConfig.key) return logs;
  return [...logs].sort((a, b) => {
    const aValue = getValueFromObject(a, sortConfig.key);
    const bValue = getValueFromObject(b, sortConfig.key);
    if (aValue < bValue) return sortConfig.direction === "asc" ? -1 : 1;
    if (aValue > bValue) return sortConfig.direction === "asc" ? 1 : -1;
    return 0;
  });
};

export const extractFieldOptions = (logs) => {
  const fieldOptions = {};

  const extractFieldsRecursively = (obj, prefix = "") => {
    Object.keys(obj).forEach((key) => {
      const fullPath = prefix ? `${prefix}.${key}` : key;
      const value = obj[key];
      if (typeof value === "object" && value !== null) {
        extractFieldsRecursively(value, fullPath);
      } else {
        if (!fieldOptions[fullPath]) {
          fieldOptions[fullPath] = new Set();
        }
        fieldOptions[fullPath].add(value);
      }
    });
  };

  logs.forEach((log) => extractFieldsRecursively(log));
  return Object.fromEntries(Object.entries(fieldOptions).map(([key, value]) => [key, [...value]]));
};
