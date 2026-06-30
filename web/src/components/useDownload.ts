export function useDownload() {
  return async (url: string, filename: string) => {
    const r = await fetch(url);
    if (!r.ok) {
      let detail = "Download failed";
      try {
        const text = await r.text();
        const j = JSON.parse(text);
        detail = j.detail ?? detail;
      } catch {}
      console.error("Download failed:", detail);
      return;
    }
    const blob = await r.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
  };
}
