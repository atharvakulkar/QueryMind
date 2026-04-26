import type { UploadedTableInfo, UploadResponse } from '@/types';

export class UploadError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UploadError';
  }
}

/**
 * Upload a CSV file to the backend.
 */
export async function uploadCSV(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('/api/v1/upload', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      let message = 'Upload failed.';
      try {
        const errorData = await response.json();
        message = errorData.detail || errorData.error?.message || message;
      } catch {
        // Fallback to text if not JSON
        const text = await response.text();
        if (text) message = text;
      }
      throw new UploadError(message);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof UploadError) throw error;
    throw new UploadError(
      error instanceof Error ? error.message : 'Network error during upload.'
    );
  }
}

/**
 * List all uploaded datasets.
 */
export async function listUploads(): Promise<UploadedTableInfo[]> {
  try {
    const response = await fetch('/api/v1/uploads');
    if (!response.ok) {
      throw new Error(`Failed to list uploads: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('List uploads failed:', error);
    return [];
  }
}

/**
 * Drop an uploaded dataset.
 */
export async function deleteUpload(tableName: string): Promise<void> {
  const response = await fetch(`/api/v1/uploads/${tableName}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    let message = 'Failed to delete table.';
    try {
      const errorData = await response.json();
      message = errorData.detail || errorData.error?.message || message;
    } catch {} // eslint-disable-line no-empty
    throw new Error(message);
  }
}
