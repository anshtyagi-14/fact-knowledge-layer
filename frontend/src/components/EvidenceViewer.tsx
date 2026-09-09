
import { X } from 'lucide-react';
import PageViewer from './PageViewer';

interface EvidenceViewerProps {
  fact: any;
  onClose: () => void;
}

export default function EvidenceViewer({ fact, onClose }: EvidenceViewerProps) {
  if (!fact) return null;
  const imageUrl = `http://localhost:8000/documents/${fact.document_id}/pages/${fact.page_number}/image`;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-8">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl h-full max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-4 border-b">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Evidence Viewer</h2>
            <p className="text-sm text-gray-500">Document: {fact.document_title} — Page {fact.page_number}</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-full">
            <X size={24} />
          </button>
        </div>
        
        <div className="flex-1 overflow-hidden flex bg-gray-100">
          <div className="flex-[2] overflow-y-auto p-4 flex justify-center border-r">
             <div className="w-full max-w-3xl shadow-lg bg-white">
                <PageViewer imageUrl={imageUrl} activeBbox={fact.evidence_bbox} />
             </div>
          </div>
          <div className="flex-[1] p-6 bg-white overflow-y-auto">
             <h3 className="text-lg font-semibold mb-4">Extracted Fact Details</h3>
             <div className="space-y-4">
                <div>
                  <div className="text-sm text-gray-500 font-medium">Subject</div>
                  <div className="text-gray-900">{fact.subject}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500 font-medium">Predicate</div>
                  <div className="text-gray-900 font-mono text-sm">{fact.predicate}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500 font-medium">Value</div>
                  <div className="text-gray-900">{fact.raw_value} (Canonical: {fact.canonical_value} {fact.canonical_unit})</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500 font-medium">Time / Scope</div>
                  <div className="text-gray-900">{fact.time_raw} / {fact.scope_segment}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500 font-medium">Evidence Text</div>
                  <div className="text-gray-900 italic bg-yellow-50 border border-yellow-200 p-3 rounded mt-1">"{fact.evidence_text}"</div>
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}
