import { Box, Flex, Text } from "@chakra-ui/react";
import { Link as RouterLink } from "react-router-dom";
import { motion } from "framer-motion";
import { Zap, Upload, CalendarDays, PenLine, ArrowRight } from "lucide-react";

import type { CatalogPlatform, IntegrationMethod } from "../../data/platformCatalog";
import { staggerItem } from "../layout/motion";

interface PlatformBrowseCardProps {
  platform: CatalogPlatform;
}

const methodMeta: Record<IntegrationMethod, { Icon: typeof Zap; label: string; color: string }> = {
  api: { Icon: Zap, label: "API", color: "var(--chakra-colors-moss-500)" },
  csv: { Icon: Upload, label: "CSV", color: "var(--chakra-colors-azure-500)" },
  year: { Icon: CalendarDays, label: "PDF", color: "var(--chakra-colors-gold-500)" },
  manual: { Icon: PenLine, label: "Handmatig", color: "var(--chakra-colors-taupe-500)" },
};

export default function PlatformBrowseCard({ platform }: PlatformBrowseCardProps) {
  const method = platform.methods[0];
  const meta = methodMeta[method];

  const caption =
    method === "api"
      ? "Koppeling aanmaken"
      : method === "csv"
        ? "Bestand uploaden"
        : method === "year"
          ? "Jaaropgave uploaden"
          : "Handmatig invoegen";

  return (
    <motion.div variants={staggerItem} whileHover={{ y: -3 }} transition={{ duration: 0.18 }}>
      <Box
        as={RouterLink}
        to={`/platforms/add?platform=${platform.id}`}
        display="block"
        p={5}
        bg="paper"
        border="1px solid"
        borderColor="line.soft"
        borderRadius="md"
        h="full"
        boxShadow="sm"
        transition="all 0.2s ease"
        _hover={{
          borderColor: "azure.300",
          boxShadow: "0 8px 28px -4px rgba(26, 58, 92, 0.12)",
          textDecoration: "none",
        }}
      >
        <Flex align="center" gap={1.5} mb={3}>
          <Box style={{ color: meta.color }} display="flex">
            <meta.Icon size={11} strokeWidth={2.25} />
          </Box>
          <Text fontSize="9px" letterSpacing="0.14em" textTransform="uppercase" color="ink.faint">
            {platform.typeLabel.split(" · ").slice(0, 1).join("")} · {meta.label}
          </Text>
        </Flex>

        <Text fontFamily="heading" fontSize="lg" fontWeight={500} mb={2} color="ink.primary">
          {platform.name}
        </Text>

        <Text fontSize="xs" color="ink.dim" lineHeight={1.7} mb={4} noOfLines={3}>
          {platform.features[0]} · {platform.integrationNote}
        </Text>

        <Flex align="center" gap={1} color="azure.500">
          <Text fontSize="xs" fontWeight={600}>
            {caption}
          </Text>
          <ArrowRight size={11} strokeWidth={2.5} />
        </Flex>
      </Box>
    </motion.div>
  );
}
