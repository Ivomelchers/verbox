import { type ReactNode } from "react";
import { Box, Table, type TableProps } from "@chakra-ui/react";

import FiscalCard from "./FiscalCard";

interface FiscalTableProps extends TableProps {
  children: ReactNode;
  toolbar?: ReactNode;
}

export default function FiscalTable({ children, toolbar, ...tableProps }: FiscalTableProps) {
  return (
    <FiscalCard elevated p={0} overflow="hidden">
      {toolbar && (
        <Box
          px={5}
          py={3}
          borderBottom="1px solid"
          borderColor="line.soft"
          bg="backgroundCard"
        >
          {toolbar}
        </Box>
      )}
      <Box overflowX="auto">
        <Table
          size="sm"
          variant="simple"
          sx={{
            "th, td": {
              fontVariantNumeric: "tabular-nums",
              fontFeatureSettings: '"tnum" 1',
            },
            th: {
              fontFamily: "body",
              fontSize: "10px",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              color: "ink.faint",
              fontWeight: 700,
              borderColor: "line.soft",
              bg: "backgroundCard",
              py: 3,
            },
            td: {
              borderColor: "line.soft",
              py: "10px",
            },
            "tbody tr": {
              transition: "background 0.12s ease",
            },
            "tbody tr:hover": {
              bg: "azure.50",
            },
            "tbody tr:last-child td": {
              borderBottom: "none",
            },
          }}
          {...tableProps}
        >
          {children}
        </Table>
      </Box>
    </FiscalCard>
  );
}
