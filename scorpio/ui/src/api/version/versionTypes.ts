/** GET /version: local CLI version and latest project release tag. */
export type ProjectVersions = {
  scorpio_cli: string | null;
  scorpio_project: string;
};
