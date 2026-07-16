"use client";
//Datei läuft im Browser, nicht auf Serverseite
import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

//
//File Context
type FileCtx = {
  file: File | null;
  setFile: (f: File | null) => void;
  fileUrl: string | null;
  clearFile: () => void;
};

//initialise variable for FileContext
const FileContext = createContext<FileCtx | undefined>(undefined);

//create a usefull link out of a chosen file
export function FileProvider({ children }: { children: React.ReactNode }) {
  const [file, setFile] = useState<File | null>(null);

  const fileUrl = useMemo(() => {
    if (!file) return null;
    return URL.createObjectURL(file);
  }, [file]);

  useEffect(() => {
    //CleanUp function -> return befor new UseEffect is executed or when component is unmounted
    return () => {
      //if fileUrl exists, URLS.revoke... is called
      if (fileUrl) URL.revokeObjectURL(fileUrl);
    };
    //Dependency Array-> execute after first rendering and everytime fileUrl changes
  }, [fileUrl]);

  const clearFile = () => setFile(null);

  return (
    <FileContext.Provider value={{ file, setFile, fileUrl, clearFile }}>
      {children}
    </FileContext.Provider>
  );
}

//export the function usFile, so other file can use the function

export function useFile() {
  const ctx = useContext(FileContext);
  if (!ctx)
    throw new Error(
      "useFile muss innerhalb von <FileProvider> verwendet werden."
    );
  return ctx;
}
``;
