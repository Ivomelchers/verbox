import { useCallback, useMemo, useRef, useState } from "react";
import {
  Box,
  Button,
  Flex,
  FormControl,
  FormLabel,
  Grid,
  Input,
  Link,
  Select,
  Text,
  VStack,
} from "@chakra-ui/react";
import {
  Search,
  Zap,
  Upload,
  CalendarDays,
  CloudUpload,
  Check,
} from "lucide-react";
import { Link as RouterLink, useNavigate, useSearchParams } from "react-router-dom";

import {
  connectBitvavo,
  connectBybit,
  connectOkx,
  connectTrading212,
  connectSaxoOAuth,
  pollSyncJob,
  type CsvImportResult,
} from "../api/integrations";
import CsvImportWizard, {
  formatPreviewMessage,
} from "../components/platforms/CsvImportWizard";
import AuthAlert from "../components/auth/AuthAlert";
import AuthFormField from "../components/auth/AuthFormField";
import FiscalCard from "../components/common/FiscalCard";
import FiscalDisclaimer from "../components/common/FiscalDisclaimer";
import PlatformAvatar from "../components/platforms/PlatformAvatar";
import MotionSection from "../components/layout/MotionSection";
import PageHeader from "../components/layout/PageHeader";
import PageShell from "../components/layout/PageShell";
import {
  PLATFORM_CATALOG,
  type CatalogPlatform,
  type IntegrationMethod,
} from "../data/platformCatalog";
import { LIVE_API_PLATFORMS, LIVE_CSV_PLATFORMS } from "../utils/platformLabels";
import { useUser } from "../contexts/UserContext";
import { getApiErrorMessage } from "../utils/apiError";

// ── Step indicator ────────────────────────────────────────────────────────────

function StepLabel({ number, label }: { number: string; label: string }) {
  return (
    <Flex align="center" gap={3} mb={5}>
      <Flex
        align="center"
        justify="center"
        w="26px"
        h="26px"
        borderRadius="full"
        border="1.5px solid"
        borderColor="azure.500"
        fontSize="10px"
        fontWeight={700}
        letterSpacing="0.05em"
        color="azure.500"
        flexShrink={0}
      >
        {number}
      </Flex>
      <Box w="16px" h="1px" bg="line.soft" flexShrink={0} />
      <Text
        fontSize="10px"
        fontWeight={700}
        letterSpacing="0.12em"
        textTransform="uppercase"
        color="ink.dim"
      >
        {label}
      </Text>
    </Flex>
  );
}

// ── Method cards config ───────────────────────────────────────────────────────

const METHOD_CARDS = [
  {
    method: "api" as IntegrationMethod,
    Icon: Zap,
    label: "API-koppeling",
    name: "Realtime sync",
    desc: "Verbind direct met API-key of OAuth2. Data wordt automatisch en doorlopend bijgewerkt.",
    platforms: "Bitvavo, Bybit, OKX, Trading 212, Saxo Bank",
  },
  {
    method: "csv" as IntegrationMethod,
    Icon: Upload,
    label: "CSV-upload",
    name: "Periodieke import",
    desc: "Upload zelf een transactie-export. Ideaal voor brokers zonder API.",
    platforms: "DEGIRO, Trading 212, Trade Republic, Bybit, OKX, Saxo Bank",
  },
  {
    method: "year" as IntegrationMethod,
    Icon: CalendarDays,
    label: "Jaaroverzicht (PDF)",
    name: "Jaarlijkse import",
    desc: "Upload het jaaroverzicht dat het platform verstrekt. Eenmaal per jaar.",
    platforms: "ABN AMRO, ING, Rabobank, Meesman",
  },
];

// ── API connectors ────────────────────────────────────────────────────────────

const API_CONNECTORS = {
  bitvavo: connectBitvavo,
  bybit: connectBybit,
  okx: connectOkx,
  trading212: connectTrading212,
} as const;

type ApiPlatformId = keyof typeof API_CONNECTORS;

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AddPlatformPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useUser();

  const initialPlatform = searchParams.get("platform") ?? "";
  const initialMethod = (searchParams.get("method") as IntegrationMethod | null) ?? null;

  const [search, setSearch] = useState("");
  const [selectedPlatform, setSelectedPlatform] = useState<CatalogPlatform | null>(
    () => PLATFORM_CATALOG.find((p) => p.id === initialPlatform) ?? null,
  );
  const [selectedMethod, setSelectedMethod] = useState<IntegrationMethod | null>(initialMethod);

  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [apiPassphrase, setApiPassphrase] = useState("");
  const [okxDomain, setOkxDomain] = useState("okx.com");
  const [label, setLabel] = useState("");
  const [error, setError] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [csvWizardOpen, setCsvWizardOpen] = useState(false);
  const [csvWizardFile, setCsvWizardFile] = useState<File | null>(null);
  const [csvMessage, setCsvMessage] = useState("");
  const csvInputRef = useRef<HTMLInputElement>(null);
  const csvDropZoneRef = useRef<HTMLDivElement>(null);

  const filteredPlatforms = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) {
      return PLATFORM_CATALOG.filter(
        (p) =>
          LIVE_CSV_PLATFORMS.some((live) => live.id === p.id) ||
          LIVE_API_PLATFORMS.some((live) => live.id === p.id),
      );
    }
    return PLATFORM_CATALOG.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.searchTerms?.includes(q) ||
        p.typeLabel.toLowerCase().includes(q),
    );
  }, [search]);

  const availableMethods = selectedPlatform?.methods ?? [];
  const apiMeta = LIVE_API_PLATFORMS.find((p) => p.id === selectedPlatform?.id);
  const isLiveCsv =
    selectedPlatform != null && LIVE_CSV_PLATFORMS.some((p) => p.id === selectedPlatform.id);
  const isLiveApi = apiMeta != null;

  const handleCsvFile = useCallback((file: File) => {
    if (!file.name.endsWith(".csv")) {
      setError("Alleen CSV-bestanden worden ondersteund.");
      return;
    }
    setCsvMessage("");
    setCsvWizardFile(file);
    setCsvWizardOpen(true);
  }, []);

  const handleCsvWizardComplete = (result: CsvImportResult) => {
    setCsvMessage(formatPreviewMessage(result));
    if (csvInputRef.current) csvInputRef.current.value = "";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (csvDropZoneRef.current) {
      csvDropZoneRef.current.style.borderColor = "var(--chakra-colors-azure-400)";
      csvDropZoneRef.current.style.backgroundColor = "var(--chakra-colors-azure-50)";
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (csvDropZoneRef.current) {
      csvDropZoneRef.current.style.borderColor = "var(--chakra-colors-line-DEFAULT)";
      csvDropZoneRef.current.style.backgroundColor = "var(--chakra-colors-backgroundHover)";
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (csvDropZoneRef.current) {
      csvDropZoneRef.current.style.borderColor = "var(--chakra-colors-line-DEFAULT)";
      csvDropZoneRef.current.style.backgroundColor = "var(--chakra-colors-backgroundHover)";
    }
    const file = e.dataTransfer.files?.[0];
    if (file) handleCsvFile(file);
  };

  async function handleApiSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedPlatform || !isLiveApi) return;

    if (selectedPlatform.id === "saxo") {
      connectSaxoOAuth();
      return;
    }

    const platformId = selectedPlatform.id as ApiPlatformId;
    const connect = API_CONNECTORS[platformId];
    if (!connect) return;

    setError("");
    setStatusMessage("");
    setIsSubmitting(true);
    try {
      setStatusMessage("Verbinding controleren…");
      const connectData: any = {
        api_key: apiKey.trim(),
        api_secret: apiSecret.trim(),
        api_passphrase: apiMeta?.needsPassphrase ? apiPassphrase.trim() : undefined,
        label: label.trim() || selectedPlatform.name,
      };
      if (selectedPlatform.id === "okx") {
        connectData.domain = okxDomain;
      }
      const result = await connect(connectData);
      if (result.sync_job?.id) {
        setStatusMessage("Portfolio synchroniseren…");
        const job = await pollSyncJob(result.sync_job.id);
        if (job.status === "error") {
          setError(job.error_message || "Synchronisatie mislukt.");
          return;
        }
      }
      navigate("/platforms", {
        state: { message: `${selectedPlatform.name} succesvol gekoppeld.` },
      });
    } catch (submitError) {
      setError(getApiErrorMessage(submitError, `${selectedPlatform.name} koppelen mislukt.`));
    } finally {
      setIsSubmitting(false);
    }
  }

  const showApiForm = isLiveApi && selectedMethod === "api";

  return (
    <PageShell maxW="960px">
      <MotionSection>
        <PageHeader
          kicker={
            <Link as={RouterLink} to="/platforms" color="azure.500" fontSize="inherit">
              ← Mijn platformen
            </Link>
          }
          title={
            <>
              Nieuwe <Text as="em">databron</Text>
            </>
          }
          subtitle="Kies een platform en koppelingsmethode. CSV-imports ondersteunen auto-detectie op kolomkoppen."
        />
      </MotionSection>

      {user && !user.email_verified && (
        <MotionSection>
          <AuthAlert tone="info">
            Bevestig eerst uw e-mailadres voordat u een platform kunt koppelen.
          </AuthAlert>
        </MotionSection>
      )}

      {/* ── Step 1: Platform ──────────────────────────────────────────────── */}
      <MotionSection>
        <StepLabel number="01" label="Kies een platform" />

        <Box position="relative" mb={4}>
          <Box
            position="absolute"
            left="12px"
            top="50%"
            transform="translateY(-50%)"
            color="ink.faint"
            pointerEvents="none"
            zIndex={1}
            display="flex"
          >
            <Search size={14} strokeWidth={2} />
          </Box>
          <Input
            variant="fiscal"
            placeholder="Zoek platform…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            pl="36px"
          />
        </Box>

        <Grid templateColumns={{ base: "1fr 1fr", md: "repeat(3, 1fr)" }} gap="10px">
          {filteredPlatforms.map((platform) => {
            const active = selectedPlatform?.id === platform.id;
            return (
              <Box
                key={platform.id}
                as="button"
                type="button"
                textAlign="left"
                py={3}
                px={4}
                border="1.5px solid"
                borderColor={active ? "gold.500" : "line.soft"}
                borderRadius="base"
                bg={active ? "gold.50" : "backgroundCard"}
                position="relative"
                transition="all 0.18s ease"
                _hover={{
                  borderColor: active ? "gold.500" : "azure.400",
                  bg: active ? "gold.50" : "paper",
                  transform: "translateY(-1px)",
                  boxShadow: "0 4px 16px rgba(20,33,61,0.08)",
                }}
                onClick={() => {
                  setSelectedPlatform(platform);
                  setSelectedMethod(null);
                  setLabel(platform.name);
                }}
              >
                {active && (
                  <Box
                    position="absolute"
                    top={2}
                    right={2}
                    color="gold.500"
                    display="flex"
                  >
                    <Check size={13} strokeWidth={2.5} />
                  </Box>
                )}
                <Flex gap={3} align="center">
                  <PlatformAvatar initials={platform.initials} color={platform.color} size="sm" />
                  <Box minW={0}>
                    <Text fontWeight={600} fontSize="sm" noOfLines={1}>
                      {platform.name}
                    </Text>
                    <Text
                      fontSize="10px"
                      color="ink.faint"
                      noOfLines={1}
                      letterSpacing="0.02em"
                      mt="2px"
                    >
                      {platform.typeLabel}
                    </Text>
                  </Box>
                </Flex>
              </Box>
            );
          })}
        </Grid>
      </MotionSection>

      {/* ── Step 2: Method ────────────────────────────────────────────────── */}
      {selectedPlatform && (
        <MotionSection>
          <StepLabel number="02" label="Hoe wilt u koppelen?" />
          <Grid templateColumns={{ base: "1fr", md: "repeat(3, 1fr)" }} gap={4}>
            {METHOD_CARDS.filter((m) => availableMethods.includes(m.method)).map((card) => {
              const active = selectedMethod === card.method;
              return (
                <Box
                  key={card.method}
                  as="button"
                  type="button"
                  textAlign="left"
                  p={5}
                  border="1.5px solid"
                  borderColor={active ? "azure.500" : "line.soft"}
                  borderRadius="base"
                  bg={active ? "azure.50" : "backgroundCard"}
                  position="relative"
                  transition="all 0.2s ease"
                  _hover={{
                    borderColor: active ? "azure.500" : "azure.400",
                    bg: active ? "azure.50" : "paper",
                    transform: "translateY(-2px)",
                    boxShadow: "0 8px 28px rgba(20,33,61,0.10)",
                  }}
                  onClick={() => setSelectedMethod(card.method)}
                >
                  {active && (
                    <Box
                      position="absolute"
                      top={3}
                      right={3}
                      color="azure.500"
                      display="flex"
                    >
                      <Check size={14} strokeWidth={2.5} />
                    </Box>
                  )}
                  <Box
                    mb={4}
                    color={active ? "azure.500" : "ink.faint"}
                    display="flex"
                    transition="color 0.2s"
                  >
                    <card.Icon size={22} strokeWidth={1.5} />
                  </Box>
                  <Text
                    fontSize="10px"
                    letterSpacing="0.12em"
                    textTransform="uppercase"
                    color="ink.faint"
                    mb={1}
                  >
                    {card.label}
                  </Text>
                  <Text fontFamily="heading" fontSize="lg" mb={2} color="ink.primary">
                    {card.name}
                  </Text>
                  <Text fontSize="sm" color="ink.dim" lineHeight={1.6} mb={4}>
                    {card.desc}
                  </Text>
                  <Text fontSize="11px" color="taupe.500" lineHeight={1.6}>
                    {card.platforms}
                  </Text>
                </Box>
              );
            })}
          </Grid>
        </MotionSection>
      )}

      <MotionSection>
        <FiscalDisclaimer>
          API-koppelingen: Bitvavo, Bybit, OKX, Trading 212 en Trade Republic. Brokers zonder API:
          CSV-upload op Mijn platformen.
        </FiscalDisclaimer>
      </MotionSection>

      {/* ── API form ──────────────────────────────────────────────────────── */}
      {showApiForm && selectedPlatform && (
        <MotionSection>
          <FiscalCard elevated p={6}>
            <Text fontWeight={600} mb={4}>
              {selectedPlatform.name}{" "}
              {selectedPlatform.id === "saxo" ? "OAuth-koppeling" : "API-koppeling"}
            </Text>
            {error && <AuthAlert tone="error">{error}</AuthAlert>}
            {statusMessage && !error && <AuthAlert tone="info">{statusMessage}</AuthAlert>}

            {selectedPlatform.id === "saxo" ? (
              <VStack align="stretch" spacing={4}>
                <Text fontSize="sm" color="ink.dim" lineHeight={1.7}>
                  U wordt doorgestuurd naar Saxo Bank om in te loggen en de app goed te keuren. Na
                  goedkeuring keert u automatisch terug naar Vermogenspeil.
                </Text>
                <Button
                  onClick={(e: React.FormEvent) => handleApiSubmit(e)}
                  variant="fiscal"
                  isLoading={isSubmitting}
                  isDisabled={!user?.email_verified}
                  alignSelf="flex-start"
                >
                  Met Saxo Bank inloggen
                </Button>
              </VStack>
            ) : (
              <Box as="form" onSubmit={(e: React.FormEvent) => void handleApiSubmit(e)}>
                <VStack align="stretch" spacing={4}>
                  <AuthFormField
                    label="Label"
                    name="label"
                    value={label}
                    onChange={(e) => setLabel(e.target.value)}
                  />
                  <AuthFormField
                    label="API-key"
                    name="api_key"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    isRequired
                    autoComplete="off"
                  />
                  {apiMeta?.needsSecret && (
                    <FormControl isRequired>
                      <FormLabel fontSize="sm" color="ink.dim">
                        API-secret
                      </FormLabel>
                      <Input
                        type="password"
                        value={apiSecret}
                        onChange={(e) => setApiSecret(e.target.value)}
                        autoComplete="off"
                        variant="fiscal"
                      />
                    </FormControl>
                  )}
                  {apiMeta?.needsPassphrase && (
                    <FormControl isRequired>
                      <FormLabel fontSize="sm" color="ink.dim">
                        API-passphrase
                      </FormLabel>
                      <Input
                        type="password"
                        value={apiPassphrase}
                        onChange={(e) => setApiPassphrase(e.target.value)}
                        autoComplete="off"
                        variant="fiscal"
                      />
                    </FormControl>
                  )}
                  {selectedPlatform?.id === "okx" && (
                    <FormControl>
                      <FormLabel fontSize="sm" color="ink.dim">
                        OKX API Domein
                      </FormLabel>
                      <Select
                        value={okxDomain}
                        onChange={(e) => setOkxDomain(e.target.value)}
                        variant="fiscal"
                        fontSize="sm"
                      >
                        <option value="okx.com">okx.com (Global - www.okx.com)</option>
                        <option value="eea.okx.com">eea.okx.com (EU/Nederland - my.okx.com)</option>
                        <option value="us.okx.com">us.okx.com (US/AU - app.okx.com)</option>
                      </Select>
                      <Text fontSize="xs" color="ink.faint" mt={2}>
                        Controleer waar u zich op OKX hebt geregistreerd. Kies het bijbehorende
                        API-domein.
                      </Text>
                    </FormControl>
                  )}
                  <Button
                    type="submit"
                    variant="fiscal"
                    isLoading={isSubmitting}
                    isDisabled={
                      !user?.email_verified ||
                      !apiKey ||
                      (apiMeta?.needsSecret && !apiSecret) ||
                      (apiMeta?.needsPassphrase && !apiPassphrase)
                    }
                    alignSelf="flex-start"
                  >
                    {selectedPlatform?.name} koppelen
                  </Button>
                </VStack>
              </Box>
            )}
          </FiscalCard>
        </MotionSection>
      )}

      <input
        ref={csvInputRef}
        type="file"
        accept=".csv,text/csv"
        hidden
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) handleCsvFile(f);
        }}
      />

      {/* ── CSV drop zone ─────────────────────────────────────────────────── */}
      {selectedPlatform && selectedMethod === "csv" && isLiveCsv && (
        <MotionSection>
          <FiscalCard elevated p={6}>
            <Text fontWeight={600} mb={5}>
              {selectedPlatform.name} · CSV-import
            </Text>
            {csvMessage && (
              <Box mb={4} p={3} bg="moss.50" borderRadius="base" fontSize="sm" color="moss.700">
                {csvMessage}
              </Box>
            )}
            <Box
              ref={csvDropZoneRef}
              p={8}
              border="1.5px dashed"
              borderColor="line.DEFAULT"
              borderRadius="base"
              bg="backgroundHover"
              textAlign="center"
              transition="all 0.2s ease"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              cursor="pointer"
              onClick={() => csvInputRef.current?.click()}
              _hover={{ borderColor: "azure.400", bg: "azure.50" }}
            >
              <Flex justify="center" mb={4} color="ink.faint">
                <CloudUpload size={36} strokeWidth={1.25} />
              </Flex>
              <Text fontWeight={600} fontSize="sm" mb={1}>
                Sleep uw CSV-bestand hier
              </Text>
              <Text fontSize="sm" color="ink.faint" mb={5}>
                of klik om te selecteren
              </Text>
              <Button
                variant="fiscal"
                size="sm"
                isDisabled={!user?.email_verified}
                onClick={(e) => {
                  e.stopPropagation();
                  csvInputRef.current?.click();
                }}
                mb={5}
              >
                Bestand selecteren
              </Button>
              <Text fontSize="xs" color="ink.faint" lineHeight={1.7} maxW="360px" mx="auto">
                Ondersteunde formaten: DEGIRO, Trading 212, Trade Republic, Bybit, OKX, Saxo Bank
                en meer. We detecteren het formaat automatisch en tonen eerst een preview.
              </Text>
            </Box>
            <Flex mt={4}>
              <Link as={RouterLink} to="/platforms" fontSize="sm" color="ink.faint" _hover={{ color: "azure.500" }}>
                ← Terug naar mijn platformen
              </Link>
            </Flex>
          </FiscalCard>
        </MotionSection>
      )}

      {/* ── Fallback ──────────────────────────────────────────────────────── */}
      {selectedPlatform &&
        selectedMethod &&
        !showApiForm &&
        !(selectedMethod === "csv" && isLiveCsv) && (
          <MotionSection>
            <FiscalCard elevated p={6}>
              <Text fontWeight={600} mb={2}>
                {selectedPlatform.name} · catalogus
              </Text>
              <Text fontSize="sm" color="ink.dim" lineHeight={1.7} mb={4}>
                {selectedPlatform.description} Automatische koppeling voor deze methode volgt later.
              </Text>
              <Flex gap={2} flexWrap="wrap">
                <Button as={RouterLink} to="/portfolio/manual/asset" variant="fiscal" size="sm">
                  Handmatig asset toevoegen
                </Button>
                <Button as={RouterLink} to="/platforms/vergelijker" variant="ghostNav" size="sm">
                  Platformen vergelijken
                </Button>
              </Flex>
            </FiscalCard>
          </MotionSection>
        )}

      <CsvImportWizard
        isOpen={csvWizardOpen}
        file={csvWizardFile}
        platform={selectedPlatform?.id}
        onClose={() => {
          setCsvWizardOpen(false);
          setCsvWizardFile(null);
        }}
        onComplete={handleCsvWizardComplete}
      />
    </PageShell>
  );
}
