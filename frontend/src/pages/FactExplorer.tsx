import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Search } from 'lucide-react';
import EvidenceViewer from '../components/EvidenceViewer';

export default function FactExplorer() {
  const [predicateFilter, setPredicateFilter] = useState('');
  const [selectedFact, setSelectedFact] = useState<any>(null);

  const { data: facts = [], isLoading } = useQuery({
    queryKey: ['all_facts', predicateFilter],
    queryFn: async () => {
      const params = predicateFilter ? { predicate: predicateFilter } : {};
      const res = await axios.get(`http://localhost:8000/facts`, { params });
      return res.data;
    }
  });

  return (
    <div className="flex flex-col h-full bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h1 className="text-2xl font-bold mb-6 text-gray-900">Fact Explorer</h1>
      
      <div className="flex gap-4 mb-6">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 text-gray-400" size={20} />
          <input 
            type="text" 
            placeholder="Filter by predicate (e.g., revenue, growth)..." 
            value={predicateFilter}
            onChange={e => setPredicateFilter(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>
      </div>

      <div className="flex-1 overflow-auto border rounded-lg">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-50 sticky top-0 border-b">
            <tr>
              <th className="p-3 font-semibold text-gray-600">Document</th>
              <th className="p-3 font-semibold text-gray-600">Subject</th>
              <th className="p-3 font-semibold text-gray-600">Predicate</th>
              <th className="p-3 font-semibold text-gray-600">Value (Canonical)</th>
              <th className="p-3 font-semibold text-gray-600">Time</th>
              <th className="p-3 font-semibold text-gray-600">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {isLoading ? (
               <tr><td colSpan={6} className="p-8 text-center text-gray-500">Loading...</td></tr>
            ) : facts.length === 0 ? (
               <tr><td colSpan={6} className="p-8 text-center text-gray-500">No facts found.</td></tr>
            ) : facts.map((fact: any) => (
              <tr key={fact.id} className="hover:bg-gray-50">
                <td className="p-3 text-sm text-gray-500 truncate max-w-[150px]" title={fact.document_title}>{fact.document_title}</td>
                <td className="p-3 text-sm font-medium text-gray-900">{fact.subject}</td>
                <td className="p-3 text-sm font-mono text-gray-600">{fact.predicate}</td>
                <td className="p-3 text-sm text-gray-900">{fact.raw_value}</td>
                <td className="p-3 text-sm text-gray-500">{fact.time_raw}</td>
                <td className="p-3">
                  <button 
                    onClick={() => setSelectedFact(fact)}
                    className="text-blue-600 hover:underline text-sm font-medium"
                  >
                    View Evidence
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selectedFact && <EvidenceViewer fact={selectedFact} onClose={() => setSelectedFact(null)} />}
    </div>
  );
}
