import { type ReactNode } from "react";
import { Box, Text } from "@chakra-ui/react";

import Kicker from "./Kicker";
import MoneyText, { type MoneyTone } from "./MoneyText";

interface InsightCardProps {
  label: string;
  value: ReactNode;
  delta?: string;
  tone?: MoneyTone;
  accent?: "ochre" | "default";
}

export default function InsightCard({
  label,
  value,
  delta,
  tone = "default",
  accent = "default",
}: InsightCardProps) {
  return (
    <Box
      bg="paper"
      border="1px solid"
      borderColor="line.DEFAULT"
      borderRadius="md"
      px={5}
      py={5}
      boxShadow="sm"
      transition="border-color 0.18s ease, box-shadow 0.18s ease"
      _hover={{
        borderColor: "line.soft"  ,
        boxShadow: "0 4px 20px -4px rgba(20, 33, 61, 0.10), 0 1px 4px rgba(20, 33, 61, 0.04)",
      }}
    >
      <Kicker mb={3}>{label}</Kicker>
      {typeof value === "string" ? (
        <MoneyText
          variant="display"
          fontSize={{ base: "26px", md: "30px" }}
          tone={tone}
          color={accent === "ochre" ? "azure.500" : undefined}
          letterSpacing="-0.025em"
        >
          {value}
        </MoneyText>
      ) : (
        <Box fontFamily="heading" fontSize={{ base: "26px", md: "30px" }} letterSpacing="-0.025em">
          {value}
        </Box>
      )}
      {delta && (
        <Text
          fontSize="xs"
          mt={2}
          color={tone === "positive" ? "moss.500" : tone === "negative" ? "rust.500" : "ink.dim"}
          fontStyle="italic"
          fontFamily="heading"
        >
          {delta}
        </Text>
      )}
    </Box>
  );
}
