import { Box, Flex, SimpleGrid, Text } from "@chakra-ui/react";

export interface StatItem {
  label: string;
  value: string | number;
  sub: string;
  tone?: "default" | "moss" | "ochre";
}

interface StatStripProps {
  items: StatItem[];
  columns?: number;
}

export default function StatStrip({ items, columns = 4 }: StatStripProps) {
  return (
    <SimpleGrid columns={{ base: 2, md: columns }} spacing={4}>
      {items.map((item) => (
        <Box
          key={item.label}
          bg="paper"
          border="1px solid"
          borderColor="line.DEFAULT"
          borderRadius="md"
          px={5}
          py={5}
          boxShadow="sm"
          transition="border-color 0.18s ease, box-shadow 0.18s ease"
          _hover={{
            borderColor: "line.soft",
            boxShadow: "0 4px 20px -4px rgba(20, 33, 61, 0.10), 0 1px 4px rgba(20, 33, 61, 0.04)",
          }}
        >
          <Text
            fontSize="10px"
            letterSpacing="0.14em"
            textTransform="uppercase"
            color="ink.faint"
            mb={2}
          >
            {item.label}
          </Text>
          <Flex align="baseline" gap={1}>
            <Text
              fontFamily="heading"
              fontSize="3xl"
              lineHeight={1}
              letterSpacing="-0.03em"
              color={
                item.tone === "moss"
                  ? "moss.500"
                  : item.tone === "ochre"
                    ? "gold.500"
                    : "ink.primary"
              }
            >
              {item.value}
            </Text>
          </Flex>
          <Text fontSize="xs" color="ink.dim" mt={2}>
            {item.sub}
          </Text>
        </Box>
      ))}
    </SimpleGrid>
  );
}
