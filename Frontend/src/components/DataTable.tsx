import React from 'react';
import { TableRow } from '../services/api';

interface DataTableProps {
  data: TableRow[];
}

const DataTable: React.FC<DataTableProps> = ({ data }) => {
  if (!data || data.length === 0) return null;

  const headers = Object.keys(data[0]);

  return (
    <div className="data-container">
      <table className="w-full text-left">
        <thead>
          <tr>
            {headers.map((header) => (
              <th key={header} className="whitespace-nowrap">
                {header.replace(/_/g, ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx} className="hover:bg-orange-50/50 transition-colors">
              {headers.map((header) => (
                <td key={`${idx}-${header}`}>
                  {typeof row[header] === 'boolean' 
                    ? (row[header] ? '✅ Yes' : '❌ No') 
                    : row[header]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;
