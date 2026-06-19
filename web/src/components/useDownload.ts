export function useDownload() {
  return async (url: string, filename: string) => {
    const r = await fetch(url);
    if (!r.ok) {
      const text = await r.text();
      let detail = "Download failed";
      try {
        const j = JSON.parse(text);
        detail = j.detail ?? detail;
      } catch {}
      throw new Error(detail);
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
