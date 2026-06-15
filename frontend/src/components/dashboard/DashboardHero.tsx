import { Box, Flex, Grid, Text } from "@chakra-ui/react";
import { TrendingUp, TrendingDown } from "lucide-react";

import type { DashboardHeroDelta, DashboardSummary } from "../../api/portfolio";
import type { ForfaitairBox3Summary } from "../../api/tax";
import type { PeildatumSnapshot } from "../../api/snapshots";
import DisplayMoney from "../portfolio/DisplayMoney";
import Kicker from "../common/Kicker";
import TaxPanelCard from "./TaxPanelCard";
import { formatDateNl, formatEur } from "../../utils/formatMoney";

interface DashboardHeroProps {
  greetingName: string;
  summary: DashboardSummary | null;
  loading: boolean;
  taxYear: number;
  forfaitair: ForfaitairBox3Summary | null;
  peildatum: PeildatumSnapshot | null;
  hasPositions: boolean;
  snapshotBusy: boolean;
  onCreatePeildatum: () => void;
  snapshotMessage?: string;
}

function HeroDelta({ delta }: { delta: DashboardHeroDelta }) {
  if (!delta.available) return null;
  const change = parseFloat(delta.change_eur ?? "0");
  const up = change >= 0;
  const Icon = up ? TrendingUp : TrendingDown;

  return (
    <Flex align="center" gap={5} mt={5} flexWrap="wrap">
      <Flex
        align="center"
        gap={2}
        px={3}
        py={1.5}
        borderRadius="base"
        bg={up ? "moss.50" : "rust.50"}
        border="1px solid"
        borderColor={up ? "moss.500" : "rust.500"}
        sx={{ fontFeatureSettings: '"tnum" 1', fontVariantNumeric: "tabular-nums" }}
        color={up ? "moss.500" : "rust.500"}
        fontSize="sm"
        fontWeight={600}
      >
        <Box display="flex" opacity={0.9}>
          <Icon size={14} strokeWidth={2.25} />
        </Box>
        <Text as="span">{formatEur(delta.change_eur ?? "0")}</Text>
        <Text as="span" opacity={0.8} fontSize="xs">
          ({up ? "+" : ""}{delta.change_percent}%)
        </Text>
      </Flex>
      <Kicker color="ink.faint" letterSpacing="0.1em">
        afgelopen 30 dagen
      </Kicker>
    </Flex>
  );
}

export default function DashboardHero({
  greetingName,
  summary,
  loading,
  taxYear,
  forfaitair,
  peildatum,
  hasPositions,
  snapshotBusy,
  onCreatePeildatum,
  snapshotMessage,
}: DashboardHeroProps) {
  const todayLabel = formatDateNl(new Date().toISOString());

  return (
    <Grid
      templateColumns={{ base: "1fr", xl: "1.35fr 1fr" }}
      gap={{ base: 6, xl: 10 }}
      py={{ base: 6, md: 10 }}
      borderBottom="1px solid"
      borderColor="line.DEFAULT"
    >
      <Box>
        <Flex align="center" gap={3} mb={5}>
          <Kicker letterSpacing="0.18em">
            Welkom terug, {greetingName}
          </Kicker>
          <Box w="1px" h="10px" bg="line.DEFAULT" />
          <Kicker color="taupe.500" letterSpacing="0.1em">
            {todayLabel}
          </Kicker>
        </Flex>

        <Text
          fontFamily="heading"
          fontStyle="italic"
          fontSize="sm"
          color="ink.dim"
          mb={3}
          letterSpacing="-0.01em"
        >
          Totaal vermogen, alle platformen
        </Text>

        {loading ? (
          <Text color="ink.dim" fontSize="sm">
            Gegevens laden…
          </Text>
        ) : (
          <>
            <DisplayMoney amount={summary?.total_value_eur ?? "0"} size="hero" />
            {summary?.hero_delta_30d && <HeroDelta delta={summary.hero_delta_30d} />}
          </>
        )}
      </Box>

      <TaxPanelCard
        taxYear={taxYear}
        forfaitair={forfaitair}
        peildatum={peildatum}
        hasPositions={hasPositions}
        snapshotBusy={snapshotBusy}
        onCreatePeildatum={onCreatePeildatum}
        snapshotMessage={snapshotMessage}
      />
    </Grid>
  );
}
