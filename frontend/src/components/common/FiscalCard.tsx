import { Box, type BoxProps } from "@chakra-ui/react";

interface FiscalCardProps extends BoxProps {
  elevated?: boolean;
}

export default function FiscalCard({ children, elevated, ...props }: FiscalCardProps) {
  return (
    <Box
      bg={elevated ? "paper" : "backgroundCard"}
      border="1px solid"
      borderColor={elevated ? "line.soft" : "line.DEFAULT"}
      borderRadius="md"
      boxShadow={elevated ? "md" : "none"}
      transition="border-color 0.18s ease, box-shadow 0.18s ease, transform 0.18s ease"
      _hover={{
        borderColor: "taupe.500",
        boxShadow: elevated
          ? "0 8px 32px -6px rgba(20, 33, 61, 0.14), 0 2px 8px -2px rgba(20, 33, 61, 0.06)"
          : "sm",
      }}
      {...props}
    >
      {children}
    </Box>
  );
}
