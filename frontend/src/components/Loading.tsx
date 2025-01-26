import { Box, CircularProgress } from "@mui/material";

export function Loading() {
  return (
    <Box sx={{ display: "flex", justifyContent: "center", my: 5 }}>
      <CircularProgress />
    </Box>
  );
}
