import { useState } from 'react';

interface PageViewerProps {
  imageUrl: string;
  activeBbox?: number[] | null; // [x0, y0, x1, y1]
}

export default function PageViewer({ imageUrl, activeBbox }: PageViewerProps) {
  const [naturalWidth, setNaturalWidth] = useState<number>(1);
  const [naturalHeight, setNaturalHeight] = useState<number>(1);
  
  // Note: Since we render at 150 DPI in PyMuPDF but the original PDF bbox is in 72 DPI,
  // we need to know the original PDF page size to scale accurately. 
  // We can extract it from headers, or assume get_pixmap scales it directly.
  // Actually, PyMuPDF bbox is in points (72 points = 1 inch).
  // If we fetch the headers from the image request, we can get X-Page-Width and X-Page-Height.
  // To keep it simple, we'll fetch the image via a normal <img> tag, and assume the API sends back an image 
  // whose aspect ratio matches. We'll compute the highlight based on the provided PDF points (which we can guess based on standard A4 = 595x842)
  // For a robust implementation, the backend should provide the exact page width/height in points.
  // For now, let's use the image natural width/height and assume the API rendered it directly.
  // Wait, if DPI=150, the image is 150/72 = ~2.083x larger than the bbox coordinates.
  const SCALE_FACTOR = 150 / 72; 

  const getHighlightStyles = () => {
    if (!activeBbox || activeBbox.length !== 4) return { display: 'none' };
    const [x0, y0, x1, y1] = activeBbox;
    
    // Convert PDF points to rendered image pixels
    const px0 = x0 * SCALE_FACTOR;
    const py0 = y0 * SCALE_FACTOR;
    const pw = (x1 - x0) * SCALE_FACTOR;
    const ph = (y1 - y0) * SCALE_FACTOR;
    
    // Convert to percentage of natural image size
    const left = (px0 / naturalWidth) * 100;
    const top = (py0 / naturalHeight) * 100;
    const width = (pw / naturalWidth) * 100;
    const height = (ph / naturalHeight) * 100;

    return {
      left: `${left}%`,
      top: `${top}%`,
      width: `${width}%`,
      height: `${height}%`
    };
  };

  return (
    <div className="relative w-full border border-gray-200 shadow-sm rounded bg-gray-50 overflow-hidden">
      <img 
        src={imageUrl} 
        alt="Page" 
        className="w-full h-auto block"
        onLoad={(e) => {
          setNaturalWidth(e.currentTarget.naturalWidth);
          setNaturalHeight(e.currentTarget.naturalHeight);
        }}
      />
      {activeBbox && naturalWidth > 1 && (
        <div 
          className="absolute bg-yellow-400 bg-opacity-40 border-2 border-yellow-500 rounded-sm pointer-events-none transition-all duration-300 ease-in-out"
          style={getHighlightStyles()}
        />
      )}
    </div>
  );
}
