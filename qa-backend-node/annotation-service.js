import fs from 'fs-extra';
import path from 'path';

/**
 * Service to annotate screenshots with visual borders, circles, arrows, and text badges 
 * using the browser's native HTML5 Canvas API in a sandboxed Playwright context.
 */
export async function annotateScreenshot(browser, screenshotBuffer, annotations, type = 'border') {
  if (!annotations || annotations.length === 0) {
    return screenshotBuffer;
  }

  // Open a sandboxed blank page in the browser context to perform drawing
  const page = await browser.newPage();
  try {
    await page.goto('about:blank');
    
    const base64Image = screenshotBuffer.toString('base64');
    
    // Evaluate standard canvas operations inside browser sandbox
    const annotatedBase64 = await page.evaluate(async ({ base64, items, drawType }) => {
      const img = new Image();
      img.src = 'data:image/png;base64,' + base64;
      
      await new Promise((resolve, reject) => {
        img.onload = resolve;
        img.onerror = () => reject(new Error('Failed to load screenshot image in canvas'));
      });
      
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      
      items.forEach(item => {
        const { x, y, width, height, label, drawType: itemDrawType, color: itemColor } = item;
        if (x === undefined || y === undefined || width === undefined || height === undefined) return;
        if (width <= 0 || height <= 0) return;
        
        const currentDrawType = itemDrawType || drawType;
        const color = itemColor || '#ef4444';
        
        ctx.save();
        
        // Compute rgba for transparent fills
        let fillColor = 'rgba(239, 68, 68, 0.15)';
        if (color.startsWith('#')) {
          const hex = color.replace('#', '');
          const r = parseInt(hex.substring(0, 2), 16);
          const g = parseInt(hex.substring(2, 4), 16);
          const b = parseInt(hex.substring(4, 6), 16);
          fillColor = `rgba(${r}, ${g}, ${b}, 0.15)`;
        }
        
        // 1. Draw Highlight Marker
        ctx.strokeStyle = color;
        ctx.lineWidth = 4;
        ctx.fillStyle = fillColor;
        
        if (currentDrawType === 'circle') {
          const cx = x + width / 2;
          const cy = y + height / 2;
          const r = Math.max(width, height) / 2 + 10;
          ctx.beginPath();
          ctx.arc(cx, cy, r, 0, 2 * Math.PI);
          ctx.stroke();
          ctx.fill();
        } else if (currentDrawType === 'glow') {
          // Draw multiple shadowed/glowing boundaries
          ctx.shadowColor = color;
          ctx.shadowBlur = 15;
          ctx.fillRect(x, y, width, height);
          ctx.strokeRect(x, y, width, height);
        } else if (currentDrawType === 'heatmap') {
          const cx = x + width / 2;
          const cy = y + height / 2;
          const r = Math.max(width, height) + 30;
          const grad = ctx.createRadialGradient(cx, cy, 2, cx, cy, r);
          
          let centerColor = 'rgba(239, 68, 68, 0.8)';
          let edgeColor = 'rgba(239, 68, 68, 0)';
          if (color.startsWith('#')) {
            const hex = color.replace('#', '');
            const r = parseInt(hex.substring(0, 2), 16);
            const g = parseInt(hex.substring(2, 4), 16);
            const b = parseInt(hex.substring(4, 6), 16);
            centerColor = `rgba(${r}, ${g}, ${b}, 0.8)`;
            edgeColor = `rgba(${r}, ${g}, ${b}, 0)`;
          }
          
          grad.addColorStop(0, centerColor);
          grad.addColorStop(0.3, centerColor.replace('0.8', '0.4'));
          grad.addColorStop(1, edgeColor);
          
          ctx.fillStyle = grad;
          ctx.beginPath();
          ctx.arc(cx, cy, r, 0, 2 * Math.PI);
          ctx.fill();
        } else {
          // Default: Red Border rectangle around coordinate area
          ctx.fillRect(x, y, width, height);
          ctx.strokeRect(x, y, width, height);
        }
        
        // 2. Draw Arrow Pointer (from 40px above pointing to top center of bounding element)
        const arrowStart = { x: x + width / 2, y: Math.max(y - 45, 10) };
        const arrowEnd = { x: x + width / 2, y: Math.max(y - 5, 0) };
        
        if (y - 50 > 0 && currentDrawType !== 'heatmap') {
          ctx.strokeStyle = color;
          ctx.fillStyle = color;
          ctx.lineWidth = 3;
          
          // Arrow Line
          ctx.beginPath();
          ctx.moveTo(arrowStart.x, arrowStart.y);
          ctx.lineTo(arrowEnd.x, arrowEnd.y);
          ctx.stroke();
          
          // Arrowhead
          ctx.beginPath();
          ctx.moveTo(arrowEnd.x, arrowEnd.y);
          ctx.lineTo(arrowEnd.x - 6, arrowEnd.y - 8);
          ctx.lineTo(arrowEnd.x + 6, arrowEnd.y - 8);
          ctx.closePath();
          ctx.fill();
        }
        
        // 3. Draw Text Label Badge
        if (label && currentDrawType !== 'heatmap') {
          ctx.font = 'bold 11px sans-serif';
          const textPadding = 8;
          const textMetrics = ctx.measureText(label);
          const badgeWidth = textMetrics.width + (textPadding * 2);
          const badgeHeight = 22;
          
          // Align badge relative to arrow start
          const badgeX = Math.max(10, Math.min(canvas.width - badgeWidth - 10, arrowStart.x - badgeWidth / 2));
          const badgeY = Math.max(5, arrowStart.y - badgeHeight - 2);
          
          // Rounded error container badge
          ctx.fillStyle = color;
          ctx.beginPath();
          if (ctx.roundRect) {
            ctx.roundRect(badgeX, badgeY, badgeWidth, badgeHeight, 4);
          } else {
            ctx.rect(badgeX, badgeY, badgeWidth, badgeHeight);
          }
          ctx.fill();
          
          // Label Text
          ctx.fillStyle = '#ffffff';
          ctx.textBaseline = 'middle';
          ctx.fillText(label, badgeX + textPadding, badgeY + (badgeHeight / 2) + 1);
        }
        
        ctx.restore();
      });
      
      return canvas.toDataURL('image/png');
    }, { base64: base64Image, items: annotations, drawType: type });
    
    return Buffer.from(annotatedBase64.replace(/^data:image\/png;base64,/, ''), 'base64');
  } finally {
    await page.close();
  }
}
