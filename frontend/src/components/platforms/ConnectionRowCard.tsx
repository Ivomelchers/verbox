import { memo } from "react";
import { Box, Button, Flex, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  AlertCircle,
  Clock,
  RefreshCw,
  FileUp,
  Unplug,
  Trash2,
} from "lucide-react";

import type { PlatformConnection } from "../../api/integrations";
import { getCatalogPlatform } from "../../data/platformCatalog";
import { staggerItem } from "../layout/motion";
import PlatformAvatar from "./PlatformAvatar";
import ImportHistoryPanel from "./ImportHistoryPanel";

function relativeSync(value: string | null): string {
  if (!value) return "Nog niet gesynchroniseerd";
  const d = new Date(value);
  const diffMin = Math.floor((Date.now() - d.getTime()) / 60000);
  if (diffMin < 1) return "Zojuist";
  if (diffMin < 60) return `${diffMin} min geleden`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 48) return `${diffH} uur geleden`;
  const diffD = Math.floor(diffH / 24);
  return `${diffD} dag${diffD === 1 ? "" : "en"} geleden`;
}

function StatusBadge({ status }: { status: PlatformConnection["status"] }) {
  const isSuccess = status === "success";
  const isError = status === "error";

  const colorKey = isSuccess ? "moss.500" : isError ? "rust.500" : "gold.500";
  const Icon = isSuccess ? CheckCircle2 : isError ? AlertCircle : Clock;
  const label = isSuccess ? "Actief" : isError ? "Fout" : "Wachtend";

  return (
    <Flex align="center" gap={1.5}>
      <Box color={colorKey} display="flex" flexShrink={0}>
        <Icon size={13} strokeWidth={2.25} />
      </Box>
      <Text fontSize="xs" fontWeight={600} color={colorKey} letterSpacing="0.01em">
        {label}
      </Text>
    </Flex>
  );
}

interface ConnectionRowCardProps {
  connection: PlatformConnection;
  secondaryLine?: string;
  syncing?: boolean;
  onSync?: () => void;
  onManage?: () => void;
  onDisconnect?: () => void;
  onPurgeData?: () => void;
  primaryActionLabel?: string;
  showImportHistory?: boolean;
  onImportHistoryChanged?: () => void;
}

function ConnectionRowCardComponent({
  connection,
  secondaryLine,
  syncing,
  onSync,
  onManage,
  onDisconnect,
  onPurgeData,
  primaryActionLabel,
  showImportHistory = true,
  onImportHistoryChanged,
}: ConnectionRowCardProps) {
  const catalog = getCatalogPlatform(connection.platform);
  const initials = catalog?.initials ?? connection.display_name.slice(0, 2);
  const color = catalog?.color ?? "#2d5a3a";
  const isCsv = connection.connection_method === "csv";
  const syncTime = relativeSync(connection.last_synced_at);

  return (
    <motion.div variants={staggerItem}>
      <Box
        p={5}
        bg="paper"
        border="1px solid"
        borderColor="line.soft"
        borderRadius="md"
        boxShadow="sm"
        transition="all 0.2s ease"
        _hover={{
          borderColor: "azure.300",
          boxShadow: "0 6px 24px -4px rgba(26, 58, 92, 0.10)",
        }}
      >
        <Flex
          gap={4}
          align={{ base: "stretch", md: "center" }}
          direction={{ base: "column", md: "row" }}
        >
          <PlatformAvatar initials={initials} color={color} />

          <Box flex={1} minW={0}>
            <Text fontFamily="heading" fontSize="lg" fontWeight={500} letterSpacing="-0.02em" mb={0.5}>
              {connection.display_name}
            </Text>
            <Text fontSize="xs" color="ink.faint">
              {connection.platform_display}
              {" · "}
              {connection.connection_method_display}
              {connection.connection_method === "api" && " · view-only"}
            </Text>
          </Box>

          <Box minW={{ md: "160px" }}>
            <StatusBadge status={connection.status} />
            <Text fontSize="xs" color="ink.dim" mt={1}>
              {syncTime}
            </Text>
            {secondaryLine && (
              <Text fontSize="xs" color="ink.dim">
                {secondaryLine}
              </Text>
            )}
            {connection.last_error && (
              <Text fontSize="xs" color="rust.500" mt={1} noOfLines={2}>
                {connection.last_error}
              </Text>
            )}
          </Box>

          <Flex gap={2} flexWrap="wrap" align="center">
            {!isCsv && onSync && (
              <Button
                variant="fiscalOutline"
                size="sm"
                isLoading={syncing}
                onClick={onSync}
                leftIcon={<RefreshCw size={13} strokeWidth={2} />}
              >
                Synchroniseren
              </Button>
            )}
            {isCsv && onManage && (
              <Button
                variant="fiscal"
                size="sm"
                onClick={onManage}
                leftIcon={<FileUp size={13} strokeWidth={2} />}
              >
                {primaryActionLabel ?? "Recentere upload"}
              </Button>
            )}
            {onManage && !isCsv && (
              <Button variant="fiscalOutline" size="sm" onClick={onManage}>
                Beheren
              </Button>
            )}
            {onDisconnect && (
              <Button
                variant="fiscalOutline"
                size="sm"
                onClick={onDisconnect}
                leftIcon={<Unplug size={13} strokeWidth={2} />}
              >
                Loskoppelen
              </Button>
            )}
            {onPurgeData && (
              <Button
                variant="fiscalOutline"
                size="sm"
                color="rust.500"
                borderColor="line.DEFAULT"
                _hover={{ borderColor: "rust.500", bg: "rust.50" }}
                onClick={onPurgeData}
                leftIcon={<Trash2 size={13} strokeWidth={2} />}
              >
                Data wissen
              </Button>
            )}
          </Flex>
        </Flex>

        {showImportHistory && (
          <ImportHistoryPanel
            connection={connection}
            onChanged={onImportHistoryChanged}
          />
        )}
      </Box>
    </motion.div>
  );
}

export default memo(ConnectionRowCardComponent);
