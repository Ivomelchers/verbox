import { FormEvent, useState } from "react";
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormHelperText,
  FormLabel,
  Grid,
  Input,
  Select,
  Text,
  VStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { PackagePlus, X } from "lucide-react";

import { createManualAsset } from "../api/portfolio";
import AuthAlert from "../components/auth/AuthAlert";
import FiscalCard from "../components/common/FiscalCard";
import MotionSection from "../components/layout/MotionSection";
import PageHeader from "../components/layout/PageHeader";
import PageShell from "../components/layout/PageShell";
import { getApiErrorMessage } from "../utils/apiError";

const ASSET_TYPES = [
  { value: "stock", label: "Aandeel" },
  { value: "etf", label: "ETF" },
  { value: "crypto", label: "Crypto" },
  { value: "metal", label: "Edelmetaal" },
  { value: "cash", label: "Spaargeld" },
  { value: "fund", label: "Fonds" },
  { value: "other", label: "Overig" },
];

const CATEGORIES = [
  { value: "belegging", label: "Belegging" },
  { value: "banktegoed", label: "Banktegoed / sparen" },
  { value: "edelmetaal", label: "Edelmetaal" },
  { value: "schuld", label: "Schuld" },
  { value: "overig", label: "Overig" },
];

export default function AddManualAssetPage() {
  const navigate = useNavigate();
  const [symbol, setSymbol] = useState("");
  const [name, setName] = useState("");
  const [assetType, setAssetType] = useState("stock");
  const [category, setCategory] = useState("belegging");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await createManualAsset({
        symbol: symbol.trim(),
        name: name.trim(),
        asset_type: assetType,
        category,
      });
      void navigate("/portfolio/manual/transaction", {
        state: { message: "Asset toegevoegd. Voeg nu een transactie toe." },
      });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, "Asset toevoegen mislukt."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PageShell maxW="640px">
      <MotionSection>
        <PageHeader
          kicker="Portefeuille"
          title={
            <>
              Asset <Text as="em">handmatig</Text> toevoegen
            </>
          }
          subtitle="Voeg een nieuw instrument toe vóór u transacties registreert."
        />
      </MotionSection>

      {error && (
        <MotionSection>
          <AuthAlert tone="error">{error}</AuthAlert>
        </MotionSection>
      )}

      <MotionSection>
        <FiscalCard elevated p={7} as="form" onSubmit={(event) => void handleSubmit(event)}>
          <VStack align="stretch" spacing={5}>
            <Grid templateColumns={{ base: "1fr", sm: "1fr 1fr" }} gap={4}>
              <FormControl isRequired>
                <FormLabel fontSize="sm" fontWeight={500} color="ink.dim" mb={1.5}>
                  Symbool / ISIN
                </FormLabel>
                <Input
                  value={symbol}
                  onChange={(e) => setSymbol(e.target.value)}
                  placeholder="bijv. IWDA"
                />
                <FormHelperText fontSize="xs" color="ink.faint">
                  Tickersymbool of ISIN-code
                </FormHelperText>
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm" fontWeight={500} color="ink.dim" mb={1.5}>
                  Naam
                </FormLabel>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="bijv. iShares MSCI World"
                />
                <FormHelperText fontSize="xs" color="ink.faint">
                  Optioneel — voor herkenbaarheid
                </FormHelperText>
              </FormControl>
            </Grid>

            <Grid templateColumns={{ base: "1fr", sm: "1fr 1fr" }} gap={4}>
              <FormControl>
                <FormLabel fontSize="sm" fontWeight={500} color="ink.dim" mb={1.5}>
                  Type
                </FormLabel>
                <Select
                  variant="fiscal"
                  value={assetType}
                  onChange={(e) => setAssetType(e.target.value)}
                >
                  {ASSET_TYPES.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel fontSize="sm" fontWeight={500} color="ink.dim" mb={1.5}>
                  Vermogenscategorie (Box 3)
                </FormLabel>
                <Select
                  variant="fiscal"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                >
                  {CATEGORIES.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Box
              pt={2}
              borderTop="1px solid"
              borderColor="line.soft"
            >
              <Flex gap={3} flexWrap="wrap">
                <Button
                  type="submit"
                  variant="fiscal"
                  isLoading={loading}
                  leftIcon={<PackagePlus size={15} strokeWidth={2} />}
                >
                  Asset opslaan
                </Button>
                <Button
                  as={RouterLink}
                  to="/portfolio"
                  variant="fiscalOutline"
                  size="sm"
                  leftIcon={<X size={13} strokeWidth={2} />}
                >
                  Annuleren
                </Button>
              </Flex>
            </Box>
          </VStack>
        </FiscalCard>
      </MotionSection>
    </PageShell>
  );
}
