import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { ChevronLeft, ChevronRight, ArrowLeft } from 'lucide-react';
import PageViewer from '../components/PageViewer';
import FactSidebar from '../components/FactSidebar';

const API_URL = 'http://localhost:8000';

export default function DocumentView() {
  const { id } = useParams();
  const [currentPage, setCurrentPage] = useState(1);
  const [showUnverified, setShowUnverified] = useState(false);
  const [activeFactId, setActiveFactId] = useState<string | null>(null);
  const [activeBbox, setActiveBbox] = useState<number[] | null>(null);

  const { data: doc, isLoading: docLoading } = useQuery({
    queryKey: ['document', id],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/documents/${id}`);
      return res.data;
    }
  });

  const { data: facts = [] } = useQuery({
    queryKey: ['facts', id],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/documents/${id}/facts`);
      return res.data;
    },
    enabled: !!id
  });

  if (docLoading) return <div className="text-center py-12">Loading document...</div>;
  if (!doc) return <div className="text-center py-12 text-red-500">Document not found</div>;

  const pageFacts = facts.filter((f: any) => f.page_number === currentPage);
  const imageUrl = `${API_URL}/documents/${id}/pages/${currentPage}/image`;

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 bg-white p-4 rounded-lg shadow-sm border border-gray-100">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-gray-500 hover:text-gray-900 transition-colors">
            <ArrowLeft size={20} />
          </Link>
          <h1 className="text-xl font-bold text-gray-900">{doc.title}</h1>
          <span className="text-sm px-2 py-1 bg-gray-100 text-gray-600 rounded">
            Status: {doc.status}
          </span>
        </div>
        
        {/* Pagination Controls */}
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-1 rounded bg-gray-100 text-gray-600 hover:bg-gray-200 disabled:opacity-50"
          >
            <ChevronLeft size={20} />
          </button>
          <span className="text-sm font-medium text-gray-700">
            Page {currentPage} of {doc.page_count || '?'}
          </span>
          <button 
            onClick={() => setCurrentPage(p => Math.min(doc.page_count || 1, p + 1))}
            disabled={currentPage === (doc.page_count || 1)}
            className="p-1 rounded bg-gray-100 text-gray-600 hover:bg-gray-200 disabled:opacity-50"
          >
            <ChevronRight size={20} />
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex gap-6 flex-1 min-h-0">
        {/* Left: Page Viewer */}
        <div className="flex-[2] overflow-y-auto bg-gray-200 rounded-lg p-4 flex justify-center">
          <div className="w-full max-w-4xl shadow-lg">
             <PageViewer imageUrl={imageUrl} activeBbox={activeBbox} />
          </div>
        </div>

        {/* Right: Facts Sidebar */}
        <div className="flex-[1] min-w-[300px] h-full">
          <FactSidebar 
            facts={pageFacts}
            activeFactId={activeFactId}
            onFactClick={(id, bbox) => {
              setActiveFactId(id);
              setActiveBbox(bbox);
            }}
            showUnverified={showUnverified}
            onToggleUnverified={setShowUnverified}
          />
        </div>
      </div>
    </div>
  );
}
