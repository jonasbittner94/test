import { useEffect, useState } from "react";

export function useFileUrl() {
  const [fileUrl, setFileUrl] = useState<string | null>(null);

  useEffect(() => {
    const storedUrl = localStorage.getItem("convertedStlUrl");
    if (storedUrl) {
      setFileUrl(storedUrl);
    }
  }, []);

  return fileUrl;
}
